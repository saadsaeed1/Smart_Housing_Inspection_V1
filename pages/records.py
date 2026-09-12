from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd

import config
from data_manager import (
    PROJECT_ROOT,
    DATA_FILE,
    load_inspections,
    normalize_plot_number,
)


def show_inspection_records():
    st.header("📋 Inspection Spreadsheet & Site Directory")
    st.caption("Click any cell to edit inline. Select a row checkbox on the left to delete. Use Search by Plot to isolate properties.")

    # Multi-level Undo stack
    if "undo_history" not in st.session_state:
        st.session_state["undo_history"] = []

    df_disk = load_inspections()

    if df_disk.empty:
        st.info("No inspection records found. Add your first record from the 'New Inspection' tab.")
        return

    # --------------------------------------------------------
    # 1. Top Action & Search Bar
    # --------------------------------------------------------
    tb1, tb2, tb3, tb4 = st.columns([3, 1, 1, 1])

    with tb1:
        plot_search = st.text_input(
            "🔍 Search by Plot Number",
            placeholder="Type plot number (e.g. 40-B, 55, B-12)...",
            help="Type any plot number to filter rows in real time",
        ).strip().upper()

    with tb2:
        save_btn = st.button("💾 Save Changes", type="primary", use_container_width=True)

    with tb3:
        undo_available = len(st.session_state["undo_history"]) > 0
        undo_btn = st.button("↩️ Undo", disabled=not undo_available, use_container_width=True)

    with tb4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Handle Undo
    if undo_btn and undo_available:
        prev_df = st.session_state["undo_history"].pop()
        prev_df.to_csv(DATA_FILE, index=False)
        st.success("↩️ Reverted to previous state.")
        st.rerun()

    # --------------------------------------------------------
    # 2. Strict Type Sanitization (Fixes Float/Text Mismatch)
    # --------------------------------------------------------
    working_df = df_disk.copy()

    # A. Text/String columns: Ensure dtype is string, never float NaN
    text_fields = [
        "Plot Number", "Sector", "Construction Activity", "Level / Floor",
        "Compliance Status", "Violation Type", "Severity", "Observation",
        "Defects", "Recommended Action", "Inspector", "Owner", "Contractor",
        "Inspection ID", "Front-view Site Image", "Defect Evidence Image"
    ]
    for col in text_fields:
        if col in working_df.columns:
            working_df[col] = working_df[col].fillna("").astype(str).replace("nan", "").replace("None", "")

    # B. Date columns: Parse into datetime64 for DateColumn editor
    date_fields = ["Inspection Date", "Deadline", "Follow-up Date"]
    for col in date_fields:
        if col in working_df.columns:
            working_df[col] = pd.to_datetime(working_df[col], errors="coerce")

    # C. Boolean columns
    if "Work Stopped" in working_df.columns:
        working_df["Work Stopped"] = working_df["Work Stopped"].apply(
            lambda x: True if str(x).strip().lower() in ["true", "yes", "1"] else False
        ).astype(bool)

    # D. Number columns
    if "Progress %" in working_df.columns:
        working_df["Progress %"] = pd.to_numeric(working_df["Progress %"], errors="coerce").fillna(0.0).astype(float)

    # --------------------------------------------------------
    # 3. Filter by Plot Search
    # --------------------------------------------------------
    if plot_search:
        clean_search = normalize_plot_number(plot_search)
        working_df = working_df[
            working_df["Plot Number"].astype(str).str.upper().str.contains(clean_search, na=False)
            | working_df["Plot Number"].astype(str).str.upper().str.contains(plot_search, na=False)
        ]

    if working_df.empty:
        st.warning(f"No records match Plot '{plot_search}'. Clear the search bar to show all records.")
        return

    # Add 1-based sequential Sr. No.
    working_df = working_df.reset_index(drop=True)
    working_df.insert(0, "Sr. No.", range(1, len(working_df) + 1))

    # --------------------------------------------------------
    # 4. Interactive Spreadsheet Grid
    # --------------------------------------------------------
    column_config = {
        "Sr. No.": st.column_config.NumberColumn("Sr.", disabled=True, width="small"),
        # Hide technical database IDs and raw image paths from primary view
        "Inspection ID": None,
        "Front-view Site Image": None,
        "Defect Evidence Image": None,
        # Editable Spreadsheet Columns
        "Plot Number": st.column_config.TextColumn("Plot Number", required=True, width="small"),
        "Sector": st.column_config.SelectboxColumn("Sector", options=[""] + list(config.SECTORS), required=True, width="small"),
        "Inspection Date": st.column_config.DateColumn("Date", required=True, width="small"),
        "Construction Activity": st.column_config.SelectboxColumn("Activity", options=[""] + list(config.CONSTRUCTION_ACTIVITIES), required=True, width="medium"),
        "Level / Floor": st.column_config.SelectboxColumn("Level / Floor", options=[""] + list(config.LEVELS), width="medium"),
        "Progress %": st.column_config.NumberColumn("Progress %", min_value=0.0, max_value=100.0, step=1.0, width="small"),
        "Compliance Status": st.column_config.SelectboxColumn("Status", options=list(config.COMPLIANCE_STATUSES), required=True, width="medium"),
        "Violation Type": st.column_config.SelectboxColumn("Violation", options=list(config.VIOLATION_TYPES), width="medium"),
        "Severity": st.column_config.SelectboxColumn("Severity", options=[""] + list(config.SEVERITY_LEVELS), width="small"),
        "Work Stopped": st.column_config.CheckboxColumn("Stop Work", width="small"),
        "Deadline": st.column_config.DateColumn("Deadline", width="small"),
        "Observation": st.column_config.TextColumn("Observation", width="large"),
        "Defects": st.column_config.TextColumn("Defects", width="medium"),
        "Recommended Action": st.column_config.TextColumn("Action Required", width="medium"),
        "Inspector": st.column_config.TextColumn("Inspector", width="small"),
        "Owner": st.column_config.TextColumn("Owner", width="small"),
        "Contractor": st.column_config.TextColumn("Contractor", width="small"),
    }

    # Render interactive spreadsheet with dynamic row deletion enabled
    edited_df = st.data_editor(
        working_df,
        column_config=column_config,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="main_spreadsheet_editor",
    )

    st.caption("💡 **Tip:** To delete a row, click the checkbox on the very left of the row, then press `Delete` on your keyboard or click the trash can icon at top right.")

    # --------------------------------------------------------
    # 5. Save Changes & Manage History
    # --------------------------------------------------------
    if save_btn:
        # Cache snapshot for Undo (keep last 10 actions)
        st.session_state["undo_history"].append(df_disk.copy())
        if len(st.session_state["undo_history"]) > 10:
            st.session_state["undo_history"].pop(0)

        save_df = edited_df.copy()
        if "Sr. No." in save_df.columns:
            save_df = save_df.drop(columns=["Sr. No."])

        # Convert dates back to clean ISO string format for CSV storage
        for c in date_fields:
            if c in save_df.columns:
                save_df[c] = pd.to_datetime(save_df[c], errors="coerce").dt.strftime("%Y-%m-%d").fillna("")

        # Normalize plot numbers
        if "Plot Number" in save_df.columns:
            save_df["Plot Number"] = save_df["Plot Number"].apply(normalize_plot_number)

        # Merge updates back to disk
        if not plot_search:
            master_df = save_df
        else:
            original_filtered_ids = working_df["Inspection ID"].dropna().tolist()
            remaining_filtered_ids = save_df["Inspection ID"].dropna().tolist()
            deleted_ids = set(original_filtered_ids) - set(remaining_filtered_ids)

            # Drop deleted rows
            master_df = df_disk[~df_disk["Inspection ID"].isin(deleted_ids)].copy()

            # Update modified records
            for _, row in save_df.iterrows():
                row_id = row.get("Inspection ID")
                if pd.notna(row_id) and str(row_id).strip():
                    idx = master_df.index[master_df["Inspection ID"].astype(str) == str(row_id)]
                    if len(idx) > 0:
                        for col in save_df.columns:
                            master_df.loc[idx[0], col] = row[col]
                    else:
                        master_df = pd.concat([master_df, pd.DataFrame([row])], ignore_index=True)

        master_df.to_csv(DATA_FILE, index=False)
        st.success("💾 Spreadsheet changes saved successfully!")
        st.rerun()

    st.divider()

    # --------------------------------------------------------
    # 6. Photographic Audit Proof
    # --------------------------------------------------------
    st.subheader("📸 Photographic Audit Proof")

    photo_options = {}
    for _, r in edited_df.iterrows():
        sr_val = r.get("Sr. No.", "")
        p_val = r.get("Plot Number", "")
        act_val = r.get("Construction Activity", "")
        stat_val = r.get("Compliance Status", "")
        opt_key = f"Row #{sr_val} | Plot {p_val} — {act_val} ({stat_val})"
        photo_options[opt_key] = r

    selected_key = st.selectbox("Select Row to Inspect Photos:", list(photo_options.keys()))
    record = photo_options[selected_key]

    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown("**Site Front-view (Macro)**")
        front_path = record.get("Front-view Site Image")
        if front_path and pd.notna(front_path) and str(front_path).strip():
            p_full = PROJECT_ROOT / str(front_path).strip()
            if p_full.exists():
                st.image(str(p_full), caption=f"Front View: Plot {record.get('Plot Number')}", use_container_width=True)
            else:
                st.caption("⚠️ Image file not found on disk.")
        else:
            st.caption("No front-view image logged.")

    with img_col2:
        st.markdown("**Defect Evidence (Micro)**")
        defect_path = record.get("Defect Evidence Image")
        if defect_path and pd.notna(defect_path) and str(defect_path).strip():
            p_defect = PROJECT_ROOT / str(defect_path).strip()
            if p_defect.exists():
                st.image(str(p_defect), caption="Forensic Defect Proof", use_container_width=True)
            else:
                st.caption("⚠️ Defect image file not found on disk.")
        else:
            if record.get("Compliance Status") == "Compliant":
                st.caption("⚪ Compliant inspection — no defect photo required.")
            else:
                st.caption("⚠️ Defect photo missing.")