import pandas as pd

from schema import INSPECTION_SCHEMA
from config import (
    INSPECTION_TYPES,
    CONSTRUCTION_ACTIVITIES,
    LEVELS,
    COMPLIANCE_STATUSES,
    SEVERITY_LEVELS,
    VIOLATION_TYPES,
)
from data_manager import load_inspections


CONTROLLED_VALUES = {
    "Inspection Type": INSPECTION_TYPES,
    "Construction Activity": CONSTRUCTION_ACTIVITIES,
    "Level / Floor": LEVELS,
    "Compliance Status": COMPLIANCE_STATUSES,
    "Severity": SEVERITY_LEVELS,
    "Violation Type": VIOLATION_TYPES,
}


def is_empty(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def validate_inspection(record):
    errors = []

    # --------------------------------------------------------
    # 1. Base Schema Requirements
    # --------------------------------------------------------
    for field, rules in INSPECTION_SCHEMA.items():
        if field == "Inspection ID":
            continue
        if not rules["required"]:
            continue

        value = record.get(field)
        if is_empty(value):
            errors.append(f"{field} is required.")

    # --------------------------------------------------------
    # 2. Controlled Values
    # --------------------------------------------------------
    for field, allowed_values in CONTROLLED_VALUES.items():
        value = record.get(field)
        if is_empty(value):
            continue
        if value not in allowed_values:
            errors.append(f"{field} has an invalid value: {value}")

    # --------------------------------------------------------
    # 3. Progress % Validation
    # --------------------------------------------------------
    progress = record.get("Progress %")
    if not is_empty(progress):
        try:
            progress_value = float(progress)
            if progress_value < 0 or progress_value > 100:
                errors.append("Progress % must be between 0 and 100.")
        except (TypeError, ValueError):
            errors.append("Progress % must be a numeric value between 0 and 100.")

    # --------------------------------------------------------
    # 4. Compliance & Violation Rules
    # --------------------------------------------------------
    compliance_status = record.get("Compliance Status")
    violation_type = record.get("Violation Type")
    severity = record.get("Severity")
    recommended_action = record.get("Recommended Action")

    if compliance_status == "Compliant":
        if violation_type != "No Violation":
            errors.append("For a Compliant inspection, Violation Type must be 'No Violation'.")
        if not is_empty(severity):
            errors.append("Severity should be empty for a Compliant inspection.")

    elif compliance_status in ["Minor Non-Compliance", "Major Non-Compliance"]:
        if is_empty(violation_type):
            errors.append("Violation Type is required for a non-compliant inspection.")
        elif violation_type == "No Violation":
            errors.append("A non-compliant inspection cannot have 'No Violation' as the Violation Type.")

        if is_empty(severity):
            errors.append("Severity is required for a non-compliant inspection.")

        if is_empty(recommended_action):
            errors.append("Recommended Action is required for a non-compliant inspection.")

    # --------------------------------------------------------
    # 5. Work Stopped Rules
    # --------------------------------------------------------
    work_stopped = record.get("Work Stopped")
    if work_stopped is True:
        if compliance_status == "Compliant":
            errors.append("Work Stopped cannot be Yes for a Compliant inspection.")
        if is_empty(violation_type) or violation_type == "No Violation":
            errors.append("A valid Violation Type is required when Work Stopped is Yes.")
        if is_empty(severity):
            errors.append("Severity is required when Work Stopped is Yes.")
        if is_empty(recommended_action):
            errors.append("Recommended Action is required when Work Stopped is Yes.")

    # --------------------------------------------------------
    # 6. Follow-up & Deadline Date Rules
    # --------------------------------------------------------
    follow_up_required = record.get("Follow-up Required")
    follow_up_date = record.get("Follow-up Date")
    inspection_date = record.get("Inspection Date")
    deadline = record.get("Deadline")

    if follow_up_required is True and is_empty(follow_up_date):
        errors.append("Follow-up Date is required when Follow-up Required is Yes.")
    elif follow_up_required is False and not is_empty(follow_up_date):
        errors.append("Follow-up Date should be empty when Follow-up Required is No.")

    if (compliance_status != "Compliant" or work_stopped is True) and is_empty(deadline):
        errors.append("Deadline is required for non-compliant inspections or stopped work.")

    if not is_empty(inspection_date):
        try:
            insp_dt = pd.to_datetime(inspection_date).date()
            if not is_empty(follow_up_date):
                if pd.to_datetime(follow_up_date).date() < insp_dt:
                    errors.append("Follow-up Date cannot be before Inspection Date.")
            if not is_empty(deadline):
                if pd.to_datetime(deadline).date() < insp_dt:
                    errors.append("Deadline cannot be before Inspection Date.")
        except (TypeError, ValueError):
            pass

    # --------------------------------------------------------
    # 7. Dual Photographic Evidence Logic
    # --------------------------------------------------------
    front_image = record.get("Front-view Site Image")
    defect_image = record.get("Defect Evidence Image")
    plot_number = str(record.get("Plot Number", "")).strip().upper()

    # Query existing database to check if this is the plot's baseline visit
    df_existing = load_inspections()
    is_baseline = True
    if not df_existing.empty and "Plot Number" in df_existing.columns:
        existing_plots = (
            df_existing["Plot Number"].astype(str).str.strip().str.upper().tolist()
        )
        if plot_number in existing_plots:
            is_baseline = False

    # Rule A: Front-view photo mandatory on first visit
    if is_baseline and is_empty(front_image):
        errors.append("Front-view Site Image is required for the baseline (first) inspection of a plot.")

    # Rule B: Defect evidence photo mandatory on violations
    if compliance_status in ["Minor Non-Compliance", "Major Non-Compliance"] and is_empty(defect_image):
        errors.append("Defect Evidence Image is mandatory when logging Minor or Major Non-Compliance.")

    # Rule C: Both macro and micro evidence required when halting work
    if work_stopped is True and is_empty(front_image):
        errors.append("Front-view Site Image is mandatory to document overall site condition when issuing a Stop Work order.")

    return errors