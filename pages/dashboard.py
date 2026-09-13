from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from data_manager import load_inspections, normalize_plot_number


def show_dashboard_page():
    st.header("📊 Society Overview & Executive Command Center")
    st.caption("High-level executive KPIs, cross-sector compliance matrices, site construction velocity, and recent activity logs.")

    df_raw = load_inspections()

    if df_raw.empty:
        st.info("No inspection data found on disk. Log inspections or seed records to populate the command center.")
        return

    df = df_raw.copy()

    # --------------------------------------------------------
    # 1. Data Normalization & Type Sanitization
    # --------------------------------------------------------
    df["Parsed_Date"] = pd.to_datetime(df["Inspection Date"], errors="coerce")
    df["Parsed_Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
    df["Is_Stopped"] = df["Work Stopped"].astype(str).str.strip().str.lower().isin(["true", "yes", "1"])

    if "Progress %" in df.columns:
        df["Progress_Clean"] = (
            df["Progress %"].astype(str).str.rstrip("%").str.strip()
        )
        df["Progress_Clean"] = pd.to_numeric(df["Progress_Clean"], errors="coerce").fillna(0.0).clip(0.0, 100.0)
    else:
        df["Progress_Clean"] = 0.0

    today_dt = pd.to_datetime(date.today())

    # --------------------------------------------------------
    # 2. Executive Society KPIs
    # --------------------------------------------------------
    total_logs = len(df)
    unique_plots = df["Plot Number"].nunique()
    compliant_logs = len(df[df["Compliance Status"] == "Compliant"])
    society_ftq = (compliant_logs / total_logs * 100.0) if total_logs > 0 else 100.0
    active_stops = len(df[df["Is_Stopped"] == True])
    
    overdue_notices = df[
        (df["Compliance Status"] != "Compliant") &
        (df["Parsed_Deadline"].notna()) &
        (df["Parsed_Deadline"] < today_dt)
    ]
    overdue_count = len(overdue_notices)
    avg_velocity = df.groupby("Plot Number")["Progress_Clean"].max().mean()

    # High-impact metric row
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Monitored Sites", f"{unique_plots} Plots", help="Unique active housing plots under municipal jurisdiction")
    k2.metric("Society Compliance", f"{society_ftq:.1f}%", help="First-Time Quality pass yield across all sectors")
    k3.metric("Stop Work Orders", active_stops, delta=None if active_stops == 0 else f"{active_stops} Halted", delta_color="inverse")
    k4.metric("Overdue Defaults", overdue_count, delta=None if overdue_count == 0 else f"{overdue_count} Lapsed", delta_color="inverse")
    k5.metric("Avg Site Progress", f"{avg_velocity:.1f}%", help="Average completion across all active sites")

    st.divider()

    # --------------------------------------------------------
    # 3. Spatial Sector Matrix & Compliance Distribution
    # --------------------------------------------------------
    col_g1, col_g2 = st.columns([1.6, 1.2])

    with col_g1:
        st.subheader("1. Sector Compliance & Work Halt Matrix")
        st.caption("Distribution of compliant, non-compliant, and halted plots across municipal sectors.")

        sec_summary = []
        for sec, s_df in df.groupby("Sector"):
            s_plots = s_df["Plot Number"].nunique()
            s_stops = len(s_df[s_df["Is_Stopped"] == True])
            s_minor = len(s_df[s_df["Compliance Status"] == "Minor Non-Compliance"])
            s_major = len(s_df[s_df["Compliance Status"] == "Major Non-Compliance"])
            s_comp = len(s_df[s_df["Compliance Status"] == "Compliant"])
            sec_summary.append({
                "Sector": f"Sector {sec}",
                "Compliant": s_comp,
                "Minor Issues": s_minor,
                "Major Issues": s_major,
                "Stop Work Orders": s_stops,
                "Active Sites": s_plots,
            })
        
        sec_df = pd.DataFrame(sec_summary)

        fig_sec = go.Figure()
        fig_sec.add_trace(go.Bar(x=sec_df["Sector"], y=sec_df["Compliant"], name="Compliant", marker_color="#198754"))
        fig_sec.add_trace(go.Bar(x=sec_df["Sector"], y=sec_df["Minor Issues"], name="Minor Defect", marker_color="#ffc107"))
        fig_sec.add_trace(go.Bar(x=sec_df["Sector"], y=sec_df["Major Issues"], name="Major Non-Compliance", marker_color="#fd7e14"))
        fig_sec.add_trace(go.Bar(x=sec_df["Sector"], y=sec_df["Stop Work Orders"], name="Stop Work", marker_color="#dc3545"))

        fig_sec.update_layout(
            barmode="group",
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            bargap=0.25,
        )
        st.plotly_chart(fig_sec, use_container_width=True)

    with col_g2:
        st.subheader("2. Quality Health Allocation")
        st.caption("Breakdown of total inspection findings society-wide.")

        status_counts = df["Compliance Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        color_map = {
            "Compliant": "#198754",
            "Minor Non-Compliance": "#ffc107",
            "Major Non-Compliance": "#dc3545",
        }

        fig_donut = px.pie(
            status_counts,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map=color_map,
            hole=0.55,
        )
        fig_donut.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # --------------------------------------------------------
    # 4. Critical Action Alerts & Priority Interventions
    # --------------------------------------------------------
    st.subheader("🚨 Priority Municipal Directives")
    st.caption("Plots requiring immediate departmental intervention due to active work halts or delinquent statutory cure deadlines.")

    critical_actions = df[
        (df["Is_Stopped"] == True) |
        ((df["Compliance Status"] != "Compliant") & (df["Parsed_Deadline"].notna()) & (df["Parsed_Deadline"] < today_dt))
    ].sort_values(by="Parsed_Deadline", ascending=True)

    if critical_actions.empty:
        st.success("✅ No critical enforcement bottlenecks or delinquent deadlines across society plots.")
    else:
        crit_display = []
        for _, r in critical_actions.head(6).iterrows():
            dl = r["Parsed_Deadline"]
            diff = (today_dt - dl).days if pd.notna(dl) else 0
            tag = f"Overdue ({diff}d)" if diff > 0 else "Active Halt"
            crit_display.append({
                "Plot": r["Plot Number"],
                "Sector": r["Sector"],
                "Owner": r["Owner"],
                "Contractor": r["Contractor"],
                "Violation": r["Violation Type"],
                "Severity": r["Severity"],
                "Work Stopped": "🚨 HALTED" if r["Is_Stopped"] else "No",
                "Deadline": r["Deadline"],
                "Enforcement Status": tag,
            })
        
        crit_df = pd.DataFrame(crit_display)
        st.dataframe(crit_df, use_container_width=True, hide_index=True)

    st.divider()

    # --------------------------------------------------------
    # 5. Recent Field Inspection Feed
    # --------------------------------------------------------
    st.subheader("🕒 Recent Site Inspection Stream")
    st.caption("Latest verified inspection records committed to the society registry.")

    recent_df = df.sort_values(by=["Parsed_Date", "Inspection ID"], ascending=[False, False]).head(5)
    feed_cols = [
        "Inspection ID", "Inspection Date", "Plot Number", "Sector", "Contractor",
        "Construction Activity", "Level / Floor", "Progress %", "Compliance Status", "Inspector"
    ]
    available_feed = [c for c in feed_cols if c in recent_df.columns]
    
    st.dataframe(
        recent_df[available_feed],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Progress %": st.column_config.NumberColumn("Progress", format="%.0f%%"),
        }
    )