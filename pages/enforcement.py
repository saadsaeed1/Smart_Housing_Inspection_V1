from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd

import config
from data_manager import PROJECT_ROOT, DATA_FILE, load_inspections, normalize_inspection


def show_enforcement_page():
    st.header("🚨 Enforcement & Municipal Compliance Tracker")
    st.caption("Monitor active Stop Work orders, statutory rectification deadlines, and legal notice dossiers.")

    df = load_inspections()

    if df.empty:
        st.info("No inspection records available in the database.")
        return

    today = pd.to_datetime(date.today())

    # Ensure clean typing
    df["Parsed_Deadline"] = pd.to_datetime(df["Deadline"], errors="coerce")
    df["Parsed_Inspection_Date"] = pd.to_datetime(df["Inspection Date"], errors="coerce")
    df["Is_Stopped"] = df["Work Stopped"].astype(str).str.strip().str.lower().isin(["true", "yes", "1"])

    # --------------------------------------------------------
    # 1. High-Impact Visual Metric Cards
    # --------------------------------------------------------
    violations_df = df[df["Compliance Status"].isin(["Minor Non-Compliance", "Major Non-Compliance"])].copy()
    active_stops_df = df[df["Is_Stopped"] == True]
    
    overdue_df = violations_df[
        (violations_df["Parsed_Deadline"].notna()) & (violations_df["Parsed_Deadline"] < today)
    ]
    critical_df = violations_df[violations_df["Severity"].isin(["Critical", "High"])]

    # Render custom styled cards
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""<div style="background-color: #f8f9fa; border-left: 5px solid #0d6efd; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; font-size: 13px; color: #6c757d; font-weight: 600; text-transform: uppercase;">Active Violations</p>
                <h2 style="margin: 5px 0 0 0; color: #212529; font-size: 32px;">{len(violations_df)}</h2>
                <span style="font-size: 12px; color: #0d6efd;">Non-Compliant Sites</span>
            </div>""",
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""<div style="background-color: #fff5f5; border-left: 5px solid #dc3545; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; font-size: 13px; color: #dc3545; font-weight: 600; text-transform: uppercase;">Stop Work Orders</p>
                <h2 style="margin: 5px 0 0 0; color: #dc3545; font-size: 32px;">{len(active_stops_df)}</h2>
                <span style="font-size: 12px; font-weight: bold; color: #dc3545;">🚨 {len(active_stops_df)} Sites Halted</span>
            </div>""",
            unsafe_allow_html=True
        )

    with c3:
        st.markdown(
            f"""<div style="background-color: #fff9db; border-left: 5px solid #f59f00; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; font-size: 13px; color: #b26b00; font-weight: 600; text-transform: uppercase;">Overdue Deadlines</p>
                <h2 style="margin: 5px 0 0 0; color: #b26b00; font-size: 32px;">{len(overdue_df)}</h2>
                <span style="font-size: 12px; font-weight: bold; color: #b26b00;">⚠️ {len(overdue_df)} Notices Lapsed</span>
            </div>""",
            unsafe_allow_html=True
        )

    with c4:
        st.markdown(
            f"""<div style="background-color: #fdf2f8; border-left: 5px solid #d63384; padding: 15px; border-radius: 8px;">
                <p style="margin: 0; font-size: 13px; color: #d63384; font-weight: 600; text-transform: uppercase;">Critical Severity</p>
                <h2 style="margin: 5px 0 0 0; color: #d63384; font-size: 32px;">{len(critical_df)}</h2>
                <span style="font-size: 12px; color: #d63384;">Structural Hazards</span>
            </div>""",
            unsafe_allow_html=True
        )

    st.divider()

    # --------------------------------------------------------
    # 2. Enforcement Spreadsheets & Filtering Controls
    # --------------------------------------------------------
    st.subheader("📋 Enforcement Registry & Action Tracker")

    fc1, fc2, fc3, fc4 = st.columns([1.5, 1.2, 1.5, 2])

    with fc1:
        view_mode = st.selectbox("Filter Status", ["All Infractions", "Stop Work Orders Only", "Overdue Deadlines Only", "Critical/High Only"])

    with fc2:
        sec_choice = st.selectbox("Enforcement Sector", ["All Sectors"] + sorted(list(violations_df["Sector"].dropna().unique())))

    with fc3:
        con_choice = st.selectbox("Enforcement Contractor", ["All Contractors"] + sorted(list(violations_df["Contractor"].dropna().unique())))

    with fc4:
        search_kw = st.text_input("Search Plot or Owner", placeholder="e.g. 12-A, Tariq...").strip().lower()

    # Apply filters
    display_df = violations_df.copy()

    if view_mode == "Stop Work Orders Only":
        display_df = display_df[display_df["Is_Stopped"] == True]
    elif view_mode == "Overdue Deadlines Only":
        display_df = display_df[(display_df["Parsed_Deadline"].notna()) & (display_df["Parsed_Deadline"] < today)]
    elif view_mode == "Critical/High Only":
        display_df = display_df[display_df["Severity"].isin(["Critical", "High"])]

    if sec_choice != "All Sectors":
        display_df = display_df[display_df["Sector"] == sec_choice]

    if con_choice != "All Contractors":
        display_df = display_df[display_df["Contractor"] == con_choice]

    if search_kw:
        display_df = display_df[
            display_df["Plot Number"].astype(str).str.lower().str.contains(search_kw) |
            display_df["Owner"].astype(str).str.lower().str.contains(search_kw)
        ]

    if display_df.empty:
        st.success("✅ No violations matching the active filter criteria.")
    else:
        # Calculate countdown / overdue days
        def compute_deadline_tag(row):
            dl = row.get("Parsed_Deadline")
            if pd.isna(dl):
                return "No Deadline Set"
            diff = (today - dl).days
            if diff > 0:
                return f"Overdue ({diff}d ago)"
            elif diff == 0:
                return "Due Today"
            else:
                return f"Active ({abs(diff)}d left)"

        display_df["Deadline Status"] = display_df.apply(compute_deadline_tag, axis=1)

        # Spreadsheet presentation configuration
        table_cols = [
            "Inspection ID", "Plot Number", "Sector", "Owner", "Contractor",
            "Construction Activity", "Compliance Status", "Violation Type",
            "Severity", "Work Stopped", "Deadline", "Deadline Status"
        ]
        available_cols = [c for c in table_cols if c in display_df.columns]
        
        st.dataframe(
            display_df[available_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Work Stopped": st.column_config.CheckboxColumn("Stop Work"),
                "Deadline": st.column_config.DateColumn("Statutory Deadline"),
            }
        )

    st.divider()

    # --------------------------------------------------------
    # 3. Enforcement Dossier & Defect Inspection
    # --------------------------------------------------------
    st.subheader("🎯 Legal Enforcement Dossier")
    st.caption("Review official inspection evidence, violations, and mandatory rectification directives.")

    if violations_df.empty:
        st.info("No active violations to inspect.")
        return

    # Hierarchical selection by Plot
    dossier_plots = sorted(list(violations_df["Plot Number"].unique()))
    dos_c1, dos_c2 = st.columns([1, 2])

    with dos_c1:
        chosen_plot = st.selectbox("Select Plot for Evidence Audit:", dossier_plots)

    plot_violations = violations_df[violations_df["Plot Number"] == chosen_plot].sort_values(by="Inspection Date", ascending=False)
    
    dos_visit_options = {
        f"{r['Inspection ID']} ({r['Inspection Date']}) — {r['Violation Type']} [{'STOPPED' if r['Is_Stopped'] else 'ACTIVE'}]": r
        for _, r in plot_violations.iterrows()
    }

    with dos_c2:
        chosen_key = st.selectbox("Select Specific Non-Compliance Record:", list(dos_visit_options.keys()))

    target_record = dos_visit_options[chosen_key]

    # Dossier Details Layout
    d_col1, d_col2 = st.columns([1.2, 1.8])

    with d_col1:
        st.markdown(f"### Plot: `{chosen_plot}`")
        st.markdown(f"**Owner:** {target_record.get('Owner')} | **Sector:** {target_record.get('Sector')}")
        st.markdown(f"**Contractor:** {target_record.get('Contractor')}")
        st.markdown(f"**Inspection Date:** {target_record.get('Inspection Date')} (`{target_record.get('Inspection ID')}`)")
        st.markdown(f"**Reporting Inspector:** {target_record.get('Inspector')}")
        
        st.divider()
        st.markdown(f"**Violation Category:** `{target_record.get('Violation Type')}`")
        st.markdown(f"**Severity Level:** `{target_record.get('Severity')}`")
        st.markdown(f"**Compliance Status:** `{target_record.get('Compliance Status')}`")

        if target_record.get("Is_Stopped"):
            st.error("🚨 OFFICIAL STOP WORK NOTICE IN FORCE")
        else:
            st.warning("⚠️ RECTIFICATION NOTICE IN EFFECT")

        st.markdown(f"**Deadline:** `{target_record.get('Deadline')}`")
        
        dl_parsed = target_record.get("Parsed_Deadline")
        if pd.notna(dl_parsed):
            diff = (today - dl_parsed).days
            if diff > 0:
                st.error(f"Status: **Overdue by {diff} days**")
            else:
                st.info(f"Status: **{abs(diff)} days remaining**")

    with d_col2:
        st.markdown("#### Photographic Legal Evidence")
        p_img1, p_img2 = st.columns(2)

        with p_img1:
            st.caption("Site Front-view (Macro)")
            f_path = target_record.get("Front-view Site Image")
            if f_path and pd.notna(f_path) and str(f_path).strip():
                fp = PROJECT_ROOT / str(f_path).strip()
                if fp.exists():
                    st.image(str(fp), caption=f"Front View: Plot {chosen_plot}", use_container_width=True)
                else:
                    st.info("⚠️ Image file not found.")
            else:
                st.caption("No front-view image logged.")

        with p_img2:
            st.caption("Defect Evidence (Micro)")
            d_path = target_record.get("Defect Evidence Image")
            if d_path and pd.notna(d_path) and str(d_path).strip():
                dp = PROJECT_ROOT / str(d_path).strip()
                if dp.exists():
                    st.image(str(dp), caption=f"Defect: {target_record.get('Violation Type')}", use_container_width=True)
                else:
                    st.info("⚠️ Defect image file not found.")
            else:
                st.caption("No defect image logged.")

    # Rectification Instructions
    with st.expander("📄 Formal Violation Observations & Required Corrective Action", expanded=True):
        st.markdown(f"**Observation:** {target_record.get('Observation')}")
        st.markdown(f"**Specific Defects:** {target_record.get('Defects')}")
        st.markdown(f"**Mandatory Rectification:** {target_record.get('Recommended Action')}")