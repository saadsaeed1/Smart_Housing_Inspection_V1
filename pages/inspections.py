from datetime import date
import streamlit as st

import config
from data_manager import (
    load_inspections,
    add_inspection,
    normalize_inspection,
    save_evidence_image,
    normalize_plot_number,
)
from validation import validate_inspection


def show_new_inspection_form():
    st.header("📝 New Site Inspection")
    st.write("Record daily site inspections, compliance statuses, and immutable photographic evidence.")

    df_existing = load_inspections()

    # --------------------------------------------------------
    # 1. Plot Identification & Master Data Lock
    # --------------------------------------------------------
    st.subheader("1. Plot & Identity")
    col_p1, col_p2, col_p3 = st.columns(3)

    existing_plots = []
    if not df_existing.empty and "Plot Number" in df_existing.columns:
        existing_plots = sorted([p for p in df_existing["Plot Number"].dropna().unique() if str(p).strip()])

    with col_p1:
        plot_mode = st.radio("Plot Selection Mode", ["Existing Plot", "Register New Plot"], horizontal=True)
        if plot_mode == "Existing Plot" and existing_plots:
            plot_number = st.selectbox("Plot Number *", existing_plots)
            plot_records = df_existing[df_existing["Plot Number"] == plot_number]
            default_sector = plot_records.iloc[0].get("Sector", config.SECTORS[0])
            default_owner = plot_records.iloc[0].get("Owner", "")
            master_locked = True
        else:
            plot_number = st.text_input("Plot Number *", placeholder="e.g. 40-B")
            default_sector = config.SECTORS[0]
            default_owner = ""
            master_locked = False

    with col_p2:
        if master_locked:
            st.text_input("Sector *", value=default_sector, disabled=True)
            sector = default_sector
        else:
            sector = st.selectbox("Sector *", config.SECTORS)

    with col_p3:
        if master_locked:
            st.text_input("Owner *", value=default_owner, disabled=True)
            owner = default_owner
        else:
            owner = st.text_input("Owner *", placeholder="e.g. Tariq Khan")

    col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
    with col_ctx1:
        inspector = st.text_input("Inspector Name *", placeholder="e.g. Eng. Saad")
    with col_ctx2:
        inspection_date = st.date_input("Inspection Date *", value=date.today(), max_value=date.today())
    with col_ctx3:
        contractor = st.text_input("Contractor Name", placeholder="e.g. Al-Buraq Builders (Optional)")

    st.divider()

    # --------------------------------------------------------
    # 2. Construction Stage & Progress
    # --------------------------------------------------------
    st.subheader("2. Construction Progress")
    col_c1, col_c2, col_c3 = st.columns(3)

    with col_c1:
        inspection_type = st.selectbox("Inspection Type *", config.INSPECTION_TYPES)
    with col_c2:
        activity = st.selectbox("Construction Activity *", config.CONSTRUCTION_ACTIVITIES)
    with col_c3:
        level = st.selectbox("Level / Floor", config.LEVELS)

    progress = st.number_input("Progress %", min_value=0.0, max_value=100.0, value=10.0, step=1.0)

    st.divider()

    # --------------------------------------------------------
    # 3. Compliance & Observations
    # --------------------------------------------------------
    st.subheader("3. Compliance & Observations")
    observation = st.text_area("Site Observations *", placeholder="Document physical conditions, active trades, and site orderliness...")
    defects = st.text_area("Defects (Optional)", placeholder="Document observed defects, honeycombing, cracks, or layout deviations...")

    compliance_status = st.selectbox("Compliance Status *", config.COMPLIANCE_STATUSES)
    is_violation = compliance_status in ["Minor Non-Compliance", "Major Non-Compliance"]

    if is_violation:
        st.markdown("#### ⚠️ Violation Details")
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            allowed_violations = [v for v in config.VIOLATION_TYPES if v != "No Violation"]
            violation_type = st.selectbox("Violation Type *", allowed_violations)
            severity = st.selectbox("Severity *", config.SEVERITY_LEVELS)
        with v_col2:
            recommended_action = st.text_area("Recommended Action *", placeholder="Specify corrective instructions for the builder...")
    else:
        violation_type = "No Violation"
        severity = ""
        recommended_action = ""

    st.divider()

    # --------------------------------------------------------
    # 4. Enforcement & Follow-up
    # --------------------------------------------------------
    st.subheader("4. Enforcement & Follow-up")
    enf_col1, enf_col2 = st.columns(2)

    with enf_col1:
        work_stopped = st.checkbox("🚨 Work Stopped (Stop Work Order Issued)", value=False)
        follow_up_required = st.checkbox("📅 Follow-up Inspection Required?", value=False)

    with enf_col2:
        if is_violation or work_stopped:
            deadline = st.date_input("Rectification Deadline *", min_value=inspection_date)
        else:
            deadline = None

        if follow_up_required:
            follow_up_date = st.date_input("Scheduled Follow-up Date *", min_value=inspection_date)
        else:
            follow_up_date = None

    st.divider()

    # --------------------------------------------------------
    # 5. Dual Photographic Evidence
    # --------------------------------------------------------
    st.subheader("5. Photographic Evidence")
    img_col1, img_col2 = st.columns(2)

    with img_col1:
        st.markdown("**Macro: Front-view Site Image**")
        st.caption("Baseline elevation or general street-view photo.")
        front_image = st.file_uploader("Upload Front-view Photo", type=["jpg", "jpeg", "png"], key="front_uploader")
        if front_image:
            st.image(front_image, caption="Front-view Preview", width=300)

    with img_col2:
        st.markdown("**Micro: Defect Evidence Image**")
        if is_violation:
            st.caption("🔴 **MANDATORY**: Forensic photo of the reported infraction.")
        else:
            st.caption("⚪ Not required for fully compliant inspections.")
        defect_image = st.file_uploader("Upload Defect Photo", type=["jpg", "jpeg", "png"], key="defect_uploader")
        if defect_image:
            st.image(defect_image, caption="Defect Evidence Preview", width=300)

    st.divider()

    # --------------------------------------------------------
    # 6. Safe Submission Pipeline
    # --------------------------------------------------------
    if st.button("💾 Save Inspection Record", type="primary", use_container_width=True):
        clean_plot = normalize_plot_number(plot_number)

        # Assemble transient record with placeholder paths for validation
        transient_record = {
            "Inspection ID": "",
            "Inspection Date": str(inspection_date),
            "Inspector": inspector.strip(),
            "Sector": sector,
            "Plot Number": clean_plot,
            "Owner": owner.strip(),
            "Contractor": contractor.strip() if contractor else "",
            "Inspection Type": inspection_type,
            "Construction Activity": activity,
            "Level / Floor": level,
            "Progress %": progress,
            "Observation": observation.strip(),
            "Defects": defects.strip() if defects else "",
            "Compliance Status": compliance_status,
            "Violation Type": violation_type,
            "Severity": severity,
            "Recommended Action": recommended_action.strip() if recommended_action else "",
            "Work Stopped": work_stopped,
            "Deadline": str(deadline) if deadline else "",
            "Follow-up Required": follow_up_required,
            "Follow-up Date": str(follow_up_date) if follow_up_date else "",
            "Front-view Site Image": "PENDING_FILE" if front_image else "",
            "Defect Evidence Image": "PENDING_FILE" if defect_image else "",
        }

        # Step A: Validate BEFORE saving any file to disk
        normalized_check = normalize_inspection(transient_record)
        errors = validate_inspection(normalized_check)

        if errors:
            st.error("❌ Validation Failed. Rectify the following items:")
            for err in errors:
                st.write(f"- 🔴 {err}")
            return

        # Step B: Write files immutably only after validation passes
        front_path = save_evidence_image(front_image, clean_plot, "front") if front_image else ""
        defect_path = save_evidence_image(defect_image, clean_plot, "defect") if defect_image else ""

        transient_record["Front-view Site Image"] = front_path
        transient_record["Defect Evidence Image"] = defect_path

        # Step C: Save to CSV
        saved = add_inspection(transient_record)
        st.success(f"🎉 Inspection `{saved['Inspection ID']}` successfully recorded for Plot `{clean_plot}`!")
        st.rerun()