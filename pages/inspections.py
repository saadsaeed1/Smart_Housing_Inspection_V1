from pathlib import Path
import streamlit as st

from config import (
    INSPECTION_TYPES,
    CONSTRUCTION_ACTIVITIES,
    LEVELS,
    COMPLIANCE_STATUSES,
    VIOLATION_TYPES,
    SEVERITY_LEVELS,
)
from data_manager import (
    PROJECT_ROOT,
    add_inspection,
    normalize_inspection,
)
from validation import validate_inspection


def show_new_inspection_form():

    st.header("📝 New Inspection")
    st.write("Create a new housing construction inspection record.")

    # ========================================================
    # SECTION 1 — INSPECTION INFORMATION
    # ========================================================
    st.subheader("1. Inspection Information")

    col1, col2 = st.columns(2)

    with col1:
        inspection_date = st.date_input("Inspection Date *")
        inspector = st.text_input("Inspector *", placeholder="Enter inspector name")
        sector = st.text_input("Sector *", placeholder="e.g. Sector A")

    with col2:
        plot_number = st.text_input("Plot Number *", placeholder="e.g. A-101")
        inspection_type = st.selectbox("Inspection Type *", INSPECTION_TYPES)

    st.divider()

    # ========================================================
    # SECTION 2 — PROPERTY & CONSTRUCTION
    # ========================================================
    st.subheader("2. Property & Construction")

    col1, col2 = st.columns(2)

    with col1:
        owner = st.text_input("Owner *", placeholder="Enter property owner")
        contractor = st.text_input("Contractor", placeholder="Enter contractor name (optional)")
        construction_activity = st.selectbox("Construction Activity *", CONSTRUCTION_ACTIVITIES)

    with col2:
        level_floor = st.selectbox("Level / Floor", LEVELS)
        progress = st.number_input(
            "Progress %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
        )

    st.divider()

    # ========================================================
    # SECTION 3 — INSPECTION FINDINGS
    # ========================================================
    st.subheader("3. Inspection Findings")

    observation = st.text_area(
        "Observation *",
        placeholder="Describe what was observed during the inspection.",
        height=120,
    )

    defects = st.text_area(
        "Defects",
        placeholder="Describe any defects observed (if applicable).",
        height=100,
    )

    compliance_status = st.selectbox("Compliance Status *", COMPLIANCE_STATUSES)

    # Conditional Non-Compliance Inputs
    if compliance_status != "Compliant":
        st.markdown("#### ⚠️ Non-Compliance Details")

        col1, col2 = st.columns(2)

        with col1:
            violation_type = st.selectbox("Violation Type *", VIOLATION_TYPES)

        with col2:
            severity = st.selectbox("Severity *", SEVERITY_LEVELS)

        recommended_action = st.text_area(
            "Recommended Action *",
            placeholder="Describe the corrective action required.",
            height=100,
        )
    else:
        violation_type = "No Violation"
        severity = ""
        recommended_action = ""

    st.divider()

    # ========================================================
    # SECTION 4 — ENFORCEMENT & FOLLOW-UP
    # ========================================================
    st.subheader("4. Enforcement & Follow-up")

    col_enf1, col_enf2 = st.columns(2)

    with col_enf1:
        work_stopped = st.checkbox(
            "🚨 Work Stopped (Stop Work Order Issued)",
            value=False,
            help="Check if construction activity on site has been officially ordered to halt.",
        )

    with col_enf2:
        if compliance_status != "Compliant" or work_stopped:
            deadline = st.date_input(
                "Correction Deadline *",
                help="Date by which the contractor or owner must resolve the issue.",
            )
        else:
            deadline = None

    st.markdown("#### 📅 Follow-up Scheduling")

    follow_up_required = st.checkbox(
        "Follow-up Inspection Required?",
        value=False,
        help="Check if an inspector needs to re-visit this plot to verify compliance.",
    )

    if follow_up_required:
        follow_up_date = st.date_input(
            "Scheduled Follow-up Date *",
            help="The target date for the follow-up inspection.",
        )
    else:
        follow_up_date = None

    st.divider()

    # ========================================================
    # SECTION 5 — EVIDENCE & PHOTOGRAPHS (Field 22)
    # ========================================================
    st.subheader("5. Photographic Evidence")

    uploaded_image = st.file_uploader(
        "Front-view Site Image *",
        type=["jpg", "jpeg", "png"],
        help="Upload a clear front-view photo of the plot or construction activity.",
    )

    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Front-view Photo", width=350)

    st.divider()

    # ========================================================
    # SAVE INSPECTION ACTION
    # ========================================================
    if st.button("💾 Save Inspection Record", type="primary"):

        # 1. Handle image saving if provided
        image_path_str = ""
        if uploaded_image is not None:
            image_dir = PROJECT_ROOT / "assets" / "site_images"
            image_dir.mkdir(parents=True, exist_ok=True)

            safe_plot = plot_number.strip().replace("/", "_").replace("\\", "_") if plot_number else "plot"
            image_filename = f"{safe_plot}_{uploaded_image.name}"
            target_path = image_dir / image_filename

            with open(target_path, "wb") as f:
                f.write(uploaded_image.getbuffer())

            image_path_str = f"assets/site_images/{image_filename}"

        # 2. Assemble raw record dictionary (22 fields)
        raw_record = {
            "Inspection ID": "",
            "Inspection Date": inspection_date,
            "Inspector": inspector,
            "Sector": sector,
            "Plot Number": plot_number,
            "Owner": owner,
            "Contractor": contractor,
            "Inspection Type": inspection_type,
            "Construction Activity": construction_activity,
            "Level / Floor": level_floor,
            "Progress %": progress,
            "Observation": observation,
            "Defects": defects,
            "Violation Type": violation_type,
            "Severity": severity,
            "Compliance Status": compliance_status,
            "Recommended Action": recommended_action,
            "Deadline": deadline if deadline else "",
            "Work Stopped": work_stopped,
            "Follow-up Required": follow_up_required,
            "Follow-up Date": follow_up_date if follow_up_date else "",
            "Front-view Site Image": image_path_str,
        }

        # 3. Normalize record
        normalized_record = normalize_inspection(raw_record)

        # 4. Validate record against business rules
        errors = validate_inspection(normalized_record)

        # 5. Save or Show Errors
        if errors:
            st.error("❌ **Validation Failed! Please fix the following errors:**")
            for err in errors:
                st.markdown(f"- 🔴 {err}")
        else:
            saved_record = add_inspection(normalized_record)
            st.success(
                f"🎉 **Inspection successfully saved! Assigned ID: `{saved_record['Inspection ID']}`**"
            )
            st.info(
                f"📁 Record added to `data/inspection_data.csv` and photo saved to `{image_path_str}`"
            )