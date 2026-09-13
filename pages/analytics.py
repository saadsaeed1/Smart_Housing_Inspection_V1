from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config
from data_manager import load_inspections, normalize_plot_number


def show_analytics_page():
    st.header("📈 Site Quality, Compliance & Risk Analytics")
    st.caption("Civil QA/QC performance metrics, Pareto defect distribution, vertical hazard profiling, and contractor scorecards.")

    df_raw = load_inspections()

    if df_raw.empty:
        st.info("No inspection records available in the database. Log inspections to populate analytics.")
        return

    # ------------------------------------------------------------------
    # 1. Defensive Normalization & Type Sanitization
    # ------------------------------------------------------------------
    df = df_raw.copy()

    if "Inspection ID" not in df.columns:
        df["Inspection ID"] = [f"INS-{i+1:03d}" for i in range(len(df))]
    else:
        df["Inspection ID"] = df["Inspection ID"].fillna("").astype(str)

    if "Progress %" in df.columns:
        df["Progress_Clean"] = (
            df["Progress %"]
            .astype(str)
            .str.rstrip("%")
            .str.strip()
        )
        df["Progress_Clean"] = pd.to_numeric(df["Progress_Clean"], errors="coerce").fillna(0.0).clip(0.0, 100.0)
    else:
        df["Progress_Clean"] = 0.0

    df["Parsed_Date"] = pd.to_datetime(df["Inspection Date"], errors="coerce")
    df["Parsed_Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")

    df["Is_Stopped"] = df["Work Stopped"].apply(
        lambda x: True if str(x).strip().lower() in ["true", "yes", "1"] else False
    )

    string_fields = [
        "Plot Number", "Sector", "Construction Activity", "Level / Floor",
        "Compliance Status", "Violation Type", "Severity", "Inspector", "Contractor", "Owner"
    ]
    for col in string_fields:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", ""], "Unassigned")
        else:
            df[col] = "Unassigned"

    df["Plot Number"] = df["Plot Number"].apply(lambda p: normalize_plot_number(p) if p != "Unassigned" else p)

    # ------------------------------------------------------------------
    # 2. Scope Filter Bar
    # ------------------------------------------------------------------
    with st.expander("🎛️ Analytical Scope & Parameters", expanded=True):
        sf1, sf2, sf3 = st.columns([1.5, 1.5, 2])

        with sf1:
            sec_list = ["All Sectors"] + sorted([s for s in df["Sector"].unique() if s != "Unassigned"])
            selected_sector = st.selectbox("Scope Sector", sec_list)

        with sf2:
            con_list = ["All Contractors"] + sorted([c for c in df["Contractor"].unique() if c != "Unassigned"])
            selected_contractor = st.selectbox("Scope Contractor", con_list)

        with sf3:
            valid_dates = df["Parsed_Date"].dropna()
            if not valid_dates.empty and valid_dates.min().date() != valid_dates.max().date():
                date_window = st.date_input("Date Window", value=(valid_dates.min().date(), valid_dates.max().date()))
            else:
                date_window = None

    filtered_df = df.copy()
    if selected_sector != "All Sectors":
        filtered_df = filtered_df[filtered_df["Sector"] == selected_sector]
    if selected_contractor != "All Contractors":
        filtered_df = filtered_df[filtered_df["Contractor"] == selected_contractor]
    if date_window and isinstance(date_window, tuple) and len(date_window) == 2:
        start_d, end_d = date_window
        filtered_df = filtered_df[
            (filtered_df["Parsed_Date"].dt.date >= start_d) &
            (filtered_df["Parsed_Date"].dt.date <= end_d)
        ]

    st.divider()

    # ------------------------------------------------------------------
    # 3. Executive KPIs & Health Gauge
    # ------------------------------------------------------------------
    total_inspections = len(filtered_df)
    unique_plots = filtered_df[filtered_df["Plot Number"] != "Unassigned"]["Plot Number"].nunique()
    compliant_count = len(filtered_df[filtered_df["Compliance Status"] == "Compliant"])
    ftq_rate = (compliant_count / total_inspections * 100.0) if total_inspections > 0 else 100.0
    active_stops = len(filtered_df[filtered_df["Is_Stopped"] == True])

    today_dt = pd.to_datetime(date.today())
    overdue_notices = filtered_df[
        (filtered_df["Compliance Status"] != "Compliant") &
        (filtered_df["Parsed_Deadline"].notna()) &
        (filtered_df["Parsed_Deadline"] < today_dt)
    ]
    overdue_count = len(overdue_notices)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Inspections Audited", total_inspections)
    k2.metric("Active Sites", unique_plots)
    k3.metric("First-Time Quality (FTQ)", f"{ftq_rate:.1f}%", help="Percentage of inspections meeting code compliance without non-conformance notices")
    k4.metric("Stop Work Orders", active_stops, delta=None if active_stops == 0 else f"{active_stops} Active", delta_color="inverse")
    k5.metric("Overdue Rectifications", overdue_count, delta=None if overdue_count == 0 else f"{overdue_count} Defaulted", delta_color="inverse")

    st.divider()

    # ------------------------------------------------------------------
    # 4. Stage-Gate Lifecycle & Quality Gauge
    # ------------------------------------------------------------------
    g_col1, g_col2 = st.columns([1.2, 1.8])

    with g_col1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=ftq_rate,
            number={"suffix": "%", "font": {"size": 32}},
            title={"text": "First-Time Quality Yield", "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#0d6efd"},
                "steps": [
                    {"range": [0, 60], "color": "#f8d7da"},
                    {"range": [60, 85], "color": "#fff3cd"},
                    {"range": [85, 100], "color": "#d1e7dd"},
                ],
                "threshold": {"line": {"color": "#198754", "width": 4}, "thickness": 0.75, "value": 90},
            }
        ))
        fig_gauge.update_layout(height=240, margin=dict(l=20, r=20, t=30, b=10))
        st.plotly_chart(fig_gauge, use_container_width=True)

    with g_col2:
        st.markdown("##### 🏗️ Construction Stage-Gate Lifecycle")
        st.caption("Distribution of active plots across physical structural milestones.")

        def map_milestone(progress):
            if progress < 20.0:
                return "1. Sub-structure / Plinth"
            elif progress < 60.0:
                return "2. Superstructure (RCC Frame)"
            elif progress < 85.0:
                return "3. Finishing & Masonry"
            else:
                return "4. Final Handover"

        plot_max_p = filtered_df[filtered_df["Plot Number"] != "Unassigned"].groupby("Plot Number")["Progress_Clean"].max()
        stage_series = plot_max_p.apply(map_milestone).value_counts().reset_index()
        stage_series.columns = ["Stage", "Plot Count"]

        stage_order = [
            "1. Sub-structure / Plinth",
            "2. Superstructure (RCC Frame)",
            "3. Finishing & Masonry",
            "4. Final Handover",
        ]
        stage_series["Sort"] = stage_series["Stage"].apply(lambda s: stage_order.index(s) if s in stage_order else 99)
        stage_series = stage_series.sort_values(by="Sort")

        fig_stages = px.bar(
            stage_series,
            x="Plot Count",
            y="Stage",
            orientation="h",
            color="Stage",
            color_discrete_sequence=["#0d6efd", "#0dcaf0", "#ffc107", "#198754"],
            text="Plot Count",
        )
        fig_stages.update_layout(
            height=240,
            yaxis=dict(autorange="reversed"),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            bargap=0.4,
        )
        st.plotly_chart(fig_stages, use_container_width=True)

    with st.expander("💡 How to Read Quality Yield & Stage-Gate Lifecycle", expanded=False):
        st.markdown(r"""
        * **First-Time Quality (FTQ):** Measures the percentage of visits passing inspection on the first try. High scores ($\ge 85\%$) reflect strong builder compliance; scores below $70\%$ indicate frequent site defects.
        * **Stage-Gate Distribution:** Shows how many society plots are currently progressing through foundational, structural framing, or architectural finishing stages.
        """)

    st.divider()

    # ------------------------------------------------------------------
    # 5. Site Risk Priority Matrix (SRPI Watchlist)
    # ------------------------------------------------------------------
    st.subheader("1. Site Risk Priority Matrix (SRPI Watchlist)")
    st.caption("Empirical hazard index: (4 × Active Stop Work) + (3 × Critical Defect) + (2 × High Defect) + (1 × Minor Non-Compliance)")

    with st.expander("💡 How to Interpret the Site Risk Priority Index (SRPI)", expanded=False):
        st.markdown(r"""
        * **The SRPI Formula:** $(4 \times \text{Stop Work}) + (3 \times \text{Critical Defect}) + (2 \times \text{High Defect}) + (1 \times \text{Minor Defect})$
        * **Red Zone ($\ge 6$):** Severe structural hazard or municipal setback encroachment. Site requires administrative stop-work enforcement.
        * **Amber Zone ($3 - 5$):** Repeat non-compliance. Site requires mandatory re-inspection before concrete pours.
        * **Clear Zone ($< 3$):** Normal routine monitoring.
        """)

    plot_groups = filtered_df[filtered_df["Plot Number"] != "Unassigned"].groupby("Plot Number")
    risk_records = []

    sort_cols = [c for c in ["Parsed_Date", "Inspection ID"] if c in filtered_df.columns]

    for plot_id, p_df in plot_groups:
        if sort_cols:
            latest = p_df.sort_values(by=sort_cols, ascending=[False] * len(sort_cols)).iloc[0]
        else:
            latest = p_df.iloc[-1]

        stops = len(p_df[p_df["Is_Stopped"] == True])
        crit = len(p_df[p_df["Severity"] == "Critical"])
        high = len(p_df[p_df["Severity"] == "High"])
        minor = len(p_df[p_df["Compliance Status"] == "Minor Non-Compliance"])

        score = (stops * 4) + (crit * 3) + (high * 2) + minor
        max_p = p_df["Progress_Clean"].max()

        risk_records.append({
            "Plot Number": plot_id,
            "Sector": latest.get("Sector"),
            "Owner": latest.get("Owner"),
            "Contractor": latest.get("Contractor"),
            "Current Activity": latest.get("Construction Activity"),
            "Level / Floor": latest.get("Level / Floor"),
            "Progress": f"{max_p:.1f}%",
            "Stop Works": stops,
            "Total Defects": stops + crit + high + minor,
            "Risk Score": score,
            "Status": "🚨 STOP WORK" if latest.get("Is_Stopped") else ("⚠️ DEFECT" if (crit + high + minor) > 0 else "✅ CLEAR"),
        })

    risk_df = pd.DataFrame(risk_records)
    if not risk_df.empty:
        risk_df = risk_df.sort_values(by=["Risk Score", "Total Defects"], ascending=[False, False]).reset_index(drop=True)
        risk_df.insert(0, "Priority", range(1, len(risk_df) + 1))

        def style_risk(row):
            val = row.get("Risk Score", 0)
            if val >= 6:
                return ["background-color: #ffd8d8; color: #842029; font-weight: bold;"] * len(row)
            elif val >= 3:
                return ["background-color: #fff3cd; color: #664d03;"] * len(row)
            return [""] * len(row)

        st.dataframe(risk_df.style.apply(style_risk, axis=1), use_container_width=True, hide_index=True)

    st.divider()

    # ------------------------------------------------------------------
    # 6. Pareto Analysis (CII 80/20 Rule) of Construction Defects
    # ------------------------------------------------------------------
    st.subheader("2. Pareto Analysis of Site Non-Conformances (CII 80/20 Principle)")
    st.caption("Identifies the vital 20% of structural activities causing 80% of project quality risks.")

    with st.expander("💡 How to Interpret the Pareto (80/20) Chart", expanded=False):
        st.markdown(r"""
        * **The 80/20 Rule:** 80% of structural delays and rework stem from roughly 20% of defect types.
        * **Red Bars (Left Axis):** Absolute frequency of defects recorded for each violation category.
        * **Blue Curve (Right Axis):** Cumulative percentage of total project quality hazard.
        * **Action Focus:** Categories situated to the left of the **80% Cutoff Line** represent the critical trades site engineers must inspect before signing off concrete pours.
        """)

    defect_df = filtered_df[filtered_df["Compliance Status"] != "Compliant"].copy()

    if defect_df.empty:
        st.success("✅ **Clean Site Certification:** Zero structural non-conformances recorded under current filter.")
    else:
        p_col1, p_col2 = st.columns([1.6, 1.2])

        with p_col1:
            pareto_data = defect_df["Violation Type"].value_counts().reset_index()
            pareto_data.columns = ["Violation Type", "Frequency"]
            pareto_data["Cumulative Sum"] = pareto_data["Frequency"].cumsum()
            pareto_data["Cumulative %"] = (pareto_data["Cumulative Sum"] / pareto_data["Frequency"].sum()) * 100.0

            fig_pareto = make_subplots(specs=[[{"secondary_y": True}]])
            fig_pareto.add_trace(
                go.Bar(
                    x=pareto_data["Violation Type"],
                    y=pareto_data["Frequency"],
                    name="Defect Count",
                    marker_color="#dc3545",
                    text=pareto_data["Frequency"],
                    textposition="auto",
                    width=0.35 if len(pareto_data) == 1 else None,
                ),
                secondary_y=False,
            )
            fig_pareto.add_trace(
                go.Scatter(
                    x=pareto_data["Violation Type"],
                    y=pareto_data["Cumulative %"],
                    name="Cumulative %",
                    mode="lines+markers+text",
                    line=dict(color="#0d6efd", width=3),
                    text=[f"{v:.0f}%" for v in pareto_data["Cumulative %"]],
                    textposition="top center",
                ),
                secondary_y=True,
            )
            fig_pareto.add_hline(y=80, line_dash="dash", line_color="#495057", annotation_text="80% Cutoff", secondary_y=True)
            fig_pareto.update_yaxes(title_text="Defect Frequency", secondary_y=False)
            fig_pareto.update_yaxes(title_text="Cumulative Impact (%)", range=[0, 110], secondary_y=True)
            fig_pareto.update_layout(
                margin=dict(l=20, r=20, t=30, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                bargap=0.3,
            )
            st.plotly_chart(fig_pareto, use_container_width=True)

        with p_col2:
            sev_data = defect_df["Severity"].value_counts().reset_index()
            sev_data.columns = ["Severity", "Count"]
            sev_palette = {
                "Critical": "#dc3545",
                "High": "#fd7e14",
                "Medium": "#ffc107",
                "Low": "#20c997",
                "Unassigned": "#adb5bd",
            }
            fig_sev = px.pie(
                sev_data,
                names="Severity",
                values="Count",
                color="Severity",
                color_discrete_map=sev_palette,
                hole=0.45,
                title="Statutory Severity Breakdown",
            )
            fig_sev.update_layout(margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_sev, use_container_width=True)

    st.divider()

    # ------------------------------------------------------------------
    # 7. Vertical Profile & Spatial Trade Matrix
    # ------------------------------------------------------------------
    v_col1, v_col2 = st.columns([1.1, 1.4])

    with v_col1:
        st.subheader("3. Vertical Elevation Defect Density")
        st.caption("Floor-by-floor defect distribution sorted strictly by structural ascent.")

        if defect_df.empty:
            st.info("No structural defects logged.")
        else:
            lvl_counts = defect_df["Level / Floor"].value_counts().reset_index()
            lvl_counts.columns = ["Level", "Defect Count"]

            if hasattr(config, "LEVEL_HIERARCHY") and isinstance(config.LEVEL_HIERARCHY, dict):
                rank_map = config.LEVEL_HIERARCHY
            elif hasattr(config, "LEVELS") and isinstance(config.LEVELS, (list, tuple)):
                rank_map = {name: idx for idx, name in enumerate(config.LEVELS)}
            else:
                rank_map = {}

            lvl_counts["Rank"] = lvl_counts["Level"].map(rank_map).fillna(99)
            lvl_counts = lvl_counts.sort_values(by="Rank")

            fig_lvl = px.bar(
                lvl_counts,
                x="Level",
                y="Defect Count",
                color="Defect Count",
                color_continuous_scale="Reds",
                text="Defect Count",
            )
            fig_lvl.update_layout(
                xaxis_title="Vertical Floor Level",
                yaxis_title="Infractions Logged",
                margin=dict(l=10, r=10, t=20, b=10),
                bargap=0.4,
            )
            st.plotly_chart(fig_lvl, use_container_width=True)

    with v_col2:
        st.subheader("4. Spatial Sector × Trade Matrix")
        st.caption("Cross-tabulation highlighting which trades cause compliance friction by sector.")

        if defect_df.empty:
            st.info("No trade violations recorded.")
        else:
            trade_pivot = pd.crosstab(defect_df["Sector"], defect_df["Construction Activity"])
            fig_heat = px.imshow(
                trade_pivot,
                labels=dict(x="Construction Activity", y="Sector", color="Defects"),
                text_auto=True,
                color_continuous_scale="YlOrRd",
                aspect="auto",
            )
            fig_heat.update_layout(margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("💡 How to Read Vertical Elevation & Spatial Trade Matrix", expanded=False):
        st.markdown(r"""
        * **Vertical Elevation Profile:** Analyzes whether site defects concentrate during early foundation works or during upper-floor slab and frame casting.
        * **Spatial Sector $\times$ Trade Heatmap:** Pinpoints localized contractor issues (e.g., rebar spacing errors concentrated specifically in Sector B).
        """)

    st.divider()

    # ------------------------------------------------------------------
    # 8. Contractor Reliability & Rectification Aging
    # ------------------------------------------------------------------
    st.subheader("5. Contractor Reliability & Quality Performance")
    st.caption("Comparative audit of execution quality, pass percentage, and Stop Work orders per builder.")

    with st.expander("💡 How to Interpret Contractor Reliability & Rectification Aging", expanded=False):
        st.markdown(r"""
        * **Contractor Scorecard:** Highlights executing builders with low pass rates or recurring Stop Work orders. Top builders maintain $\ge 80\%$ pass yields.
        * **Rectification Aging:** Categorizes unresolved violation notices into delinquency brackets. Notices exceeding $>30$ days represent statutory legal default.
        """)

    c_col1, c_col2 = st.columns([1.5, 1.2])

    with c_col1:
        contractors = [c for c in filtered_df["Contractor"].unique() if c != "Unassigned"]
        if contractors:
            c_metrics = []
            for c_name in contractors:
                c_df = filtered_df[filtered_df["Contractor"] == c_name]
                c_tot = len(c_df)
                c_pass = len(c_df[c_df["Compliance Status"] == "Compliant"])
                c_rate = (c_pass / c_tot * 100.0) if c_tot > 0 else 0.0
                c_stops = len(c_df[c_df["Is_Stopped"] == True])
                c_defs = len(c_df[c_df["Compliance Status"] != "Compliant"])

                c_metrics.append({
                    "Contractor": c_name,
                    "Visits": c_tot,
                    "Pass Rate (%)": round(c_rate, 1),
                    "Stop Works": c_stops,
                    "Total Defects": c_defs,
                })

            c_table = pd.DataFrame(c_metrics).sort_values(by="Pass Rate (%)", ascending=True)

            fig_con = px.bar(
                c_table,
                x="Pass Rate (%)",
                y="Contractor",
                orientation="h",
                color="Pass Rate (%)",
                color_continuous_scale="Blues",
                text="Pass Rate (%)",
                title="Builder Quality Yield (First-Time Pass Rate %)",
            )
            fig_con.update_layout(
                xaxis=dict(range=[0, 105]),
                yaxis_title=None,
                margin=dict(l=10, r=10, t=30, b=10),
                bargap=0.3,
            )
            st.plotly_chart(fig_con, use_container_width=True)

            st.dataframe(c_table.sort_values(by="Pass Rate (%)", ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("No contractors logged under active filter.")

    with c_col2:
        st.markdown("##### Rectification Notice Aging Defaults")
        if defect_df.empty:
            st.info("No active defect rectifications pending.")
        else:
            def categorize_aging(row):
                dl = row.get("Parsed_Deadline")
                if pd.isna(dl):
                    return "No Deadline Set"
                days_over = (today_dt - dl).days
                if days_over <= 0:
                    return "Within Window"
                elif days_over <= 7:
                    return "1–7 Days Overdue"
                elif days_over <= 14:
                    return "8–14 Days Overdue"
                elif days_over <= 30:
                    return "15–30 Days Overdue"
                else:
                    return ">30 Days Critical Default"

            defect_df["Aging_Bracket"] = defect_df.apply(categorize_aging, axis=1)
            aging_counts = defect_df["Aging_Bracket"].value_counts().reset_index()
            aging_counts.columns = ["Aging Bracket", "Notices"]

            order = [
                "Within Window",
                "1–7 Days Overdue",
                "8–14 Days Overdue",
                "15–30 Days Overdue",
                ">30 Days Critical Default",
                "No Deadline Set",
            ]
            aging_counts["Sort"] = aging_counts["Aging Bracket"].apply(lambda x: order.index(x) if x in order else 99)
            aging_counts = aging_counts.sort_values(by="Sort")

            fig_aging = px.bar(
                aging_counts,
                x="Aging Bracket",
                y="Notices",
                color="Aging Bracket",
                color_discrete_sequence=["#198754", "#ffc107", "#fd7e14", "#dc3545", "#6f42c1", "#adb5bd"],
                text="Notices",
            )
            fig_aging.update_layout(
                xaxis_title="Notice Status",
                yaxis_title="Unresolved Notices",
                showlegend=False,
                margin=dict(l=10, r=10, t=20, b=10),
                bargap=0.4,
            )
            st.plotly_chart(fig_aging, use_container_width=True)