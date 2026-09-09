
import streamlit as st

from config import (
    INSPECTION_TYPES,
    CONSTRUCTION_ACTIVITIES,
    LEVELS,
    COMPLIANCE_STATUSES,
    VIOLATION_TYPES,
    SEVERITY_LEVELS,
)


def show_new_inspection_form():

    st.header("📝 New Inspection")
    st.write("Create a new housing construction inspection record.")

    # ========================================================
    # SECTION 1 — INSPECTION INFORMATION
    # ========================================================

    st.subheader("1. Inspection Information")

    col1, col2 = st.columns(2)

    with col1:

        inspection_date = st.date_input(
            "Inspection Date *"
        )

        inspector = st.text_input(
            "Inspector *",
            placeholder="Enter inspector name"
        )

        sector = st.text_input(
            "Sector *",
            placeholder="e.g. Sector A"
        )

    with col2:

        plot_number = st.text_input(
            "Plot Number *",
            placeholder="e.g. A-101"
        )

        inspection_type = st.selectbox(
            "Inspection Type *",
            INSPECTION_TYPES
        )

    st.divider()

    # ========================================================
    # SECTION 2 — PROPERTY & CONSTRUCTION
    # ========================================================

    st.subheader("2. Property & Construction")

    col1, col2 = st.columns(2)

    with col1:

        owner = st.text_input(
            "Owner *",
            placeholder="Enter property owner"
        )

        contractor = st.text_input(
            "Contractor",
            placeholder="Enter contractor name (optional)"
        )

        construction_activity = st.selectbox(
            "Construction Activity *",
            CONSTRUCTION_ACTIVITIES
        )

    with col2:

        level_floor = st.selectbox(
            "Level / Floor",
            LEVELS
        )

        progress = st.number_input(
            "Progress %",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0
        )

    st.divider()

    # ========================================================
    # SECTION 3 — INSPECTION FINDINGS
    # ========================================================

    st.subheader("3. Inspection Findings")

    observation = st.text_area(
        "Observation *",
        placeholder="Describe what was observed during the inspection.",
        height=120
    )

    defects = st.text_area(
        "Defects",
        placeholder="Describe any defects observed (if applicable).",
        height=100
    )

    compliance_status = st.selectbox(
        "Compliance Status *",
        COMPLIANCE_STATUSES
    )

    # --------------------------------------------------------
    # CONDITIONAL NON-COMPLIANCE FIELDS
    # --------------------------------------------------------

    if compliance_status != "Compliant":

        st.markdown("#### ⚠️ Non-Compliance Details")

        col1, col2 = st.columns(2)

        with col1:

            violation_type = st.selectbox(
                "Violation Type *",
                VIOLATION_TYPES
            )

        with col2:

            severity = st.selectbox(
                "Severity *",
                SEVERITY_LEVELS
            )

        recommended_action = st.text_area(
            "Recommended Action *",
            placeholder="Describe the corrective action required.",
            height=100
        )

    else:

        # Keep variables available for later form submission
        violation_type = "No Violation"
        severity = ""
        recommended_action = ""

    st.divider()

    # ========================================================
    # TEMPORARY TEST BUTTON
    # ========================================================

    if st.button(
        "Test Findings",
        type="primary"
    ):

        st.success("🟢 Inspection Findings UI is working.")

        st.write("### Test Values")

        st.write({
            "Observation": observation,
            "Defects": defects,
            "Compliance Status": compliance_status,
            "Violation Type": violation_type,
            "Severity": severity,
            "Recommended Action": recommended_action,
        })
