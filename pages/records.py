from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd

import config
from data_manager import (
    PROJECT_ROOT,
    DATA_FILE,
    load_inspections,
    normalize_inspection,
    normalize_plot_number,
)
from validation import validate_inspection


def show_inspection_records():
    st.header("📋 Inspection Spreadsheet & Site Directory")
    st.caption("Filter records, perform inline edits, manage plot records, and audit forensic site photos.")

    if "undo_history" not in st.session_state:
        st.session_state["undo_history"] = []

    df_disk = load_inspections()

    if df_disk.empty:
        st.info("No inspection records found. Log your first inspection in 'New Inspection'.")
        return

    # --------------------------------------------------------
    # 1. Multi-Parameter Directory Filters
    # --------------------------------------------------------
    with st.expander("🔍 Filter Directory & Search Parameters", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns([1.5, 1.2, 1.5, 1.5])

        with f_col1:
            search_plot = st.text_input(
                "Plot Number Search",
                placeholder="e.g. 12-A, 35-B...",
            ).strip().upper()

        with f_col2:
            sec_options = ["All Sectors"] + sorted([s for s in df_disk["Sector"].dropna().unique() if str(s).strip()])
            selected_sector = st.selectbox("Sector", sec_options)

        with f_col3:
            con_options = ["All Contractors"] + sorted([c for c in df_disk["Contractor"].dropna().unique() if str(c).strip()])
            selected_contractor = st.selectbox("Contractor", con_options)

        with f_col4:
            stat_options = ["All Statuses"] + sorted([s for s in df_disk["Compliance Status"].dropna().unique() if str(s).strip()])
            selected_status = st.selectbox("Compliance Status", stat_options)

    # --------------------------------------------------------
    # 2. Data Filtering & Type Sanitization
    # --------------------------------------------------------
    working_df = df_disk.copy()

    # Text fields sanitization
    text_fields = [
        "Plot Number", "Sector", "Construction Activity", "Level / Floor",
        "Compliance Status", "Violation Type", "Severity", "Observation",
        "Defects", "Recommended Action", "Inspector", "Owner", "Contractor",
        "Inspection ID", "Front-view Site Image", "Defect Evidence Image"
    ]
    for col in text_fields:
        if col in working_df.columns:
            working_df[col] = working_df[col].fillna("").astype(str).replace(["nan", "None"], "")

    # Date fields
    date_fields = ["Inspection Date", "Deadline", "Follow-up Date"]
    for col in date_fields:
        if col in working_df.columns:
            working_df[col] = pd.to_datetime(working_df[col], errors="coerce")

    # Booleans & Numbers
    if "Work Stopped" in working_df.columns:
        working_df["Work Stopped"] = working_df["Work Stopped"].apply(
            lambda x: True if str(x).strip().lower() in ["true", "yes", "1"] else False
        ).astype(bool)

    if "Progress %" in working_df.columns:
        working_df["Progress %"] = pd.to_numeric(working_df["Progress %"], errors="coerce").fillna(0.0).astype(float)

    # Apply filters
    if search_plot:
        clean_search = normalize_plot_number(search_plot)
        working_df = working_df[
            working_df["Plot Number"].astype(str).str.upper().str.contains(clean_search, na=False)
            | working_df["Plot Number"].astype(str).str.upper().str.contains(search_plot, na=False)
        ]

    if selected_sector != "All Sectors":
        working_df = working_df[working_df["Sector"] == selected_sector]

    if selected_contractor != "All Contractors":
        working_df = working_df[working_df["Contractor"] == selected_contractor]

    if selected_status != "All Statuses":
        working_df = working_df[working_df["Compliance Status"] == selected_status]

    if working_df.empty:
        st.warning("No records match the active filters. Adjust your search criteria.")
        return

    working_df = working_df.reset_index(drop=True)
    working_df.insert(0, "Sr. No.", range(1, len(working_df) + 1))

    # --------------------------------------------------------
    # 3. Action Toolbar (Save, Undo, Refresh, Delete Row)
    # --------------------------------------------------------
    tb1, tb2, tb3, tb4 = st.columns([1.5, 1.2, 1.2, 3])

    with tb1:
        save_btn = st.button("💾 Save Changes", type="primary", use_container_width=True)

    with tb2:
        undo_available = len(st.session_state["undo_history"]) > 0
        undo_btn = st.button("↩️ Undo", disabled=not undo_available, use_container_width=True)

    with tb3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    with tb4:
        # Explicit 1-Click Row Deletion Mechanism
        with st.popover("🗑️ Delete Specific Record"):
            st.markdown("**Select Record to Permanently Remove:**")
            del_options = {
                f"{r['Inspection ID']} | Plot {r['Plot Number']} ({r['Inspection Date'].strftime('%Y-%m-%d') if pd.notna(r['Inspection Date']) else ''} - {r['Construction Activity']})": r['Inspection ID']
                for _, r in working_df.iterrows()
            }
            target_del = st.selectbox("Record", list(del_options.keys()))
            if st.button("Confirm Permanent Deletion", type="primary"):
                target_id = del_options[target_del]
                st.session_state["undo_history"].append(df_disk.copy())
                updated_master = df_disk[df_disk["Inspection ID"].astype(str) != str(target_id)].copy()
                updated_master.to_csv(DATA_FILE, index=False)
                st.success(f"Record {target_id} deleted successfully.")
                st.rerun()

    if undo_btn and undo_available:
        prev_df = st.session_state["undo_history"].pop()
        prev_df.to_csv(DATA_FILE, index=False)
        st.success("↩️ Reverted to previous state.")
        st.rerun()

    # --------------------------------------------------------
    # 4. Interactive Spreadsheet Editor
    # --------------------------------------------------------
    column_config = {
        "Sr. No.": st.column_config.NumberColumn("Sr.", disabled=True, width="small"),
        "Inspection ID": st.column_config.TextColumn("ID", disabled=True, width="small"),
        "Front-view Site Image": None,
        "Defect Evidence Image": None,
        # Immutable Master Records
        "Plot Number": st.column_config.TextColumn("Plot", disabled=True, width="small"),
        "Sector": st.column_config.TextColumn("Sector", disabled=True, width="small"),
        "Owner": st.column_config.TextColumn("Owner", disabled=True, width="medium"),
        # Editable Field Operations
        "Inspection Date": st.column_config.DateColumn("Date", required=True, width="small"),
        "Inspector": st.column_config.TextColumn("Inspector", width="small"),
        "Contractor": st.column_config.TextColumn("Contractor", width="medium"),
        "Construction Activity": st.column_config.SelectboxColumn("Activity", options=list(config.CONSTRUCTION_ACTIVITIES), required=True, width="medium"),
        "Level / Floor": st.column_config.SelectboxColumn("Level / Floor", options=list(config.LEVELS), width="medium"),
        "Progress %": st.column_config.NumberColumn("Progress %", min_value=0.0, max_value=100.0, step=1.0, width="small"),
        "Compliance Status": st.column_config.SelectboxColumn("Status", options=list(config.COMPLIANCE_STATUSES), required=True, width="medium"),
        "Violation Type": st.column_config.SelectboxColumn("Violation", options=list(config.VIOLATION_TYPES), width="medium"),
        "Severity": st.column_config.SelectboxColumn("Severity", options=[""] + list(config.SEVERITY_LEVELS), width="small"),
        "Work Stopped": st.column_config.CheckboxColumn("Stop Work", width="small"),
        "Deadline": st.column_config.DateColumn("Deadline", width="small"),
        "Observation": st.column_config.TextColumn("Observation", width="large"),
        "Defects": st.column_config.TextColumn("Defects", width="medium"),
        "Recommended Action": st.column_config.TextColumn("Action Required", width="medium"),
    }

    # Setting num_rows="dynamic" enables native checkbox row selection & keyboard deletion
    edited_df = st.data_editor(
        working_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="main_spreadsheet_editor",
    )

    st.caption("💡 **Spreadsheet Tips:** Double-click any cell to edit inline. To delete rows natively, check the box on the left of any row and press `Delete` on your keyboard, or use the **Delete Specific Record** button above.")

    # --------------------------------------------------------
    # 5. Commit Changes
    # --------------------------------------------------------
    if save_btn:
        save_df = edited_df.copy()
        if "Sr. No." in save_df.columns:
            save_df = save_df.drop(columns=["Sr. No."])

        # Convert dates back to string format
        for c in date_fields:
            if c in save_df.columns:
                save_df[c] = pd.to_datetime(save_df[c], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

        # Ignore accidental empty rows added via grid '+' button
        save_df = save_df[save_df["Inspection ID"].astype(str).str.strip() != ""]

        # Validate edited rows
        validation_failed = False
        row_errors = []

        for idx, row in save_df.iterrows():
            record_dict = normalize_inspection(row.to_dict())
            errs = validate_inspection(record_dict)
            if errs:
                validation_failed = True
                row_errors.append(f"Row {idx+1} (Plot {record_dict.get('Plot Number')}): {'; '.join(errs)}")

        if validation_failed:
            st.error("❌ Cannot save changes. Validation rules failed:")
            for e in row_errors:
                st.markdown(f"- {e}")
        else:
            # Snapshot for Undo
            st.session_state["undo_history"].append(df_disk.copy())
            if len(st.session_state["undo_history"]) > 10:
                st.session_state["undo_history"].pop(0)

            # Reconcile deleted rows
            orig_ids = working_df["Inspection ID"].dropna().astype(str).tolist()
            kept_ids = save_df["Inspection ID"].dropna().astype(str).tolist()
            deleted_ids = set(orig_ids) - set(kept_ids)

            master_df = df_disk[~df_disk["Inspection ID"].astype(str).isin(deleted_ids)].copy()

            # Apply row updates
            for _, row in save_df.iterrows():
                row_id = str(row.get("Inspection ID", "")).strip()
                if row_id:
                    match_idx = master_df.index[master_df["Inspection ID"].astype(str) == row_id]
                    if len(match_idx) > 0:
                        for col in save_df.columns:
                            master_df.loc[match_idx[0], col] = row[col]

            # Re-normalize and save
            clean_master = [normalize_inspection(r.to_dict()) for _, r in master_df.iterrows()]
            pd.DataFrame(clean_master).to_csv(DATA_FILE, index=False)

            st.success("💾 All spreadsheet modifications verified and saved!")
            st.rerun()

    st.divider()

    # --------------------------------------------------------
    # 6. Photographic Audit Proof (Hierarchical Selection)
    # --------------------------------------------------------
    st.subheader("📸 Photographic Audit Proof")
    st.caption("Select a plot to inspect high-resolution macro front views and micro defect evidence.")

    available_plots = sorted(list(working_df["Plot Number"].unique()))
    p_sel1, p_sel2 = st.columns([1, 2])

    with p_sel1:
        target_plot = st.selectbox("1. Select Plot Number:", available_plots)

    plot_inspections = working_df[working_df["Plot Number"] == target_plot].sort_values(by="Inspection Date", ascending=False)

    visit_options = {
        f"{r['Inspection Date'].strftime('%Y-%m-%d') if pd.notna(r['Inspection Date']) else 'Undated'} — {r['Construction Activity']} ({r['Compliance Status']})": r
        for _, r in plot_inspections.iterrows()
    }

    with p_sel2:
        target_visit_key = st.selectbox("2. Select Inspection Visit / Stage:", list(visit_options.keys()))

    record = visit_options[target_visit_key]

    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown(f"**Site Front-view (Macro): Plot {target_plot}**")
        front_path = record.get("Front-view Site Image")
        if front_path and pd.notna(front_path) and str(front_path).strip():
            p_full = PROJECT_ROOT / str(front_path).strip()
            if p_full.exists():
                st.image(str(p_full), caption=f"Macro View: Plot {target_plot} ({record.get('Construction Activity')})", use_container_width=True)
            else:
                st.info("⚠️ Image file not found on disk.")
        else:
            st.caption("No front-view image logged.")

    with img_col2:
        st.markdown("**Forensic Defect Evidence (Micro)**")
        defect_path = record.get("Defect Evidence Image")
        if defect_path and pd.notna(defect_path) and str(defect_path).strip():
            p_defect = PROJECT_ROOT / str(defect_path).strip()
            if p_defect.exists():
                st.image(str(p_defect), caption=f"Defect Proof: {record.get('Violation Type')}", use_container_width=True)
            else:
                st.info("⚠️ Defect image file not found on disk.")
        else:
            if record.get("Compliance Status") == "Compliant":
                st.success("✅ Compliant inspection — no structural defects observed.")
            else:
                st.warning("⚠️ Defect image missing from inspection record.")