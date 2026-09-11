from pathlib import Path
import streamlit as st
import pandas as pd

from data_manager import PROJECT_ROOT, load_inspections


def show_inspection_records():
    st.header("📋 Inspection Records")
    st.write("Browse, search, and audit all submitted housing inspection records.")

    df = load_inspections()

    # 1. Handle Empty State
    if df.empty or "Inspection ID" not in df.columns or df["Inspection ID"].dropna().empty:
        st.info("ℹ️ No inspection records found yet. Submit an inspection from the **New Inspection** tab to see it here.")
        return

    # 2. KPI Metrics Bar
    total_records = len(df)
    compliant_count = len(df[df["Compliance Status"] == "Compliant"])
    violations_count = len(df[df["Compliance Status"].isin(["Minor Non-Compliance", "Major Non-Compliance"])])
    stopped_count = len(df[df["Work Stopped"].astype(str).str.lower().isin(["true", "yes", "1"])])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Records", total_records)
    m2.metric("Compliant", compliant_count)
    m3.metric("Violations", violations_count)
    m4.metric("Work Stopped", stopped_count)

    st.divider()

    # 3. Interactive Filters
    st.subheader("🔍 Filter & Search")
    f_col1, f_col2, f_col3 = st.columns(3)

    sectors = ["All"] + sorted([s for s in df["Sector"].dropna().unique() if str(s).strip()])
    statuses = ["All"] + sorted([s for s in df["Compliance Status"].dropna().unique() if str(s).strip()])

    with f_col1:
        selected_sector = st.selectbox("Sector", sectors)
    with f_col2:
        selected_status = st.selectbox("Compliance Status", statuses)
    with f_col3:
        search_query = st.text_input("Search Plot Number / Owner", placeholder="e.g. A-101")

    # Apply filters
    filtered_df = df.copy()
    if selected_sector != "All":
        filtered_df = filtered_df[filtered_df["Sector"] == selected_sector]
    if selected_status != "All":
        filtered_df = filtered_df[filtered_df["Compliance Status"] == selected_status]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["Plot Number"].astype(str).str.lower().str.contains(q)
            | filtered_df["Owner"].astype(str).str.lower().str.contains(q)
        ]

    # 4. Summary Table View
    st.subheader(f"Results ({len(filtered_df)})")
    
    display_cols = [
        "Inspection ID",
        "Inspection Date",
        "Plot Number",
        "Sector",
        "Owner",
        "Inspection Type",
        "Compliance Status",
        "Work Stopped",
    ]
    available_cols = [c for c in display_cols if c in filtered_df.columns]
    st.dataframe(filtered_df[available_cols], use_container_width=True, hide_index=True)

    st.divider()

    # 5. Inspection Detail & Photo Viewer
    st.subheader("🔎 Detailed Inspection View")

    record_ids = filtered_df["Inspection ID"].dropna().tolist()
    if not record_ids:
        st.caption("No records match the current filter criteria.")
        return

    selected_id = st.selectbox("Select Inspection ID to inspect", record_ids)
    record = filtered_df[filtered_df["Inspection ID"] == selected_id].iloc[0]

    det_col1, det_col2 = st.columns([1.5, 1])

    with det_col1:
        st.markdown(f"### Plot Details: `{record.get('Plot Number', 'N/A')}`")
        st.write(f"**Inspector:** {record.get('Inspector', '—')}")
        st.write(f"**Date:** {record.get('Inspection Date', '—')}")
        st.write(f"**Sector:** {record.get('Sector', '—')} | **Floor:** {record.get('Level / Floor', '—')}")
        st.write(f"**Activity:** {record.get('Construction Activity', '—')} ({record.get('Progress %', 0)}%)")
        st.write(f"**Status:** `{record.get('Compliance Status', '—')}`")

        if record.get("Compliance Status") != "Compliant":
            st.warning(
                f"**Violation:** {record.get('Violation Type', '—')} | **Severity:** {record.get('Severity', '—')}\n\n"
                f"**Action:** {record.get('Recommended Action', '—')}\n\n"
                f"**Deadline:** {record.get('Deadline', '—')}"
            )

        if str(record.get("Work Stopped")).lower() in ["true", "yes", "1"]:
            st.error("🚨 **WORK STOPPED ORDER ISSUED**")

        if str(record.get("Follow-up Required")).lower() in ["true", "yes", "1"]:
            st.info(f"📅 **Follow-up Scheduled for:** {record.get('Follow-up Date', '—')}")

        with st.expander("Notes & Observations"):
            st.write(f"**Observation:** {record.get('Observation', 'None')}")
            st.write(f"**Defects:** {record.get('Defects', 'None')}")

    with det_col2:
        st.markdown("### Photographic Evidence")
        raw_img_path = str(record.get("Front-view Site Image", "")).strip()
        img_file = PROJECT_ROOT / raw_img_path if raw_img_path else None

        if img_file and img_file.exists() and img_file.is_file():
            st.image(str(img_file), caption=f"Evidence for {record.get('Plot Number')}", use_container_width=True)
        else:
            st.warning("⚠️ No image found on disk for this record (ephemeral session restart or file omitted).")