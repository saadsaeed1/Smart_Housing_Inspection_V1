import pandas as pd

from schema import INSPECTION_SCHEMA
from config import (
    INSPECTION_TYPES,
    CONSTRUCTION_ACTIVITIES,
    LEVELS,
    LEVEL_HIERARCHY,
    STRUCTURAL_ACTIVITIES,
    FINISHING_ACTIVITIES,
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
    # 1. Base Schema Mandatory Fields
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
    # 2. Controlled Values Check
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
    progress_value = None
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
    # 6. Dates & Chronology
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
    # 7. Dual Photographic Evidence Logic (Option B)
    # --------------------------------------------------------
    front_image = record.get("Front-view Site Image")
    defect_image = record.get("Defect Evidence Image")
    plot_number = str(record.get("Plot Number", "")).strip().upper()

    df_existing = load_inspections()
    plot_history = pd.DataFrame()
    is_baseline = True

    if not df_existing.empty and "Plot Number" in df_existing.columns:
        plot_history = df_existing[
            df_existing["Plot Number"].astype(str).str.strip().str.upper() == plot_number
        ].copy()
        if not plot_history.empty:
            is_baseline = False

    if is_baseline and is_empty(front_image):
        errors.append("Front-view Site Image is required for the baseline (first) inspection of a plot.")

    if compliance_status in ["Minor Non-Compliance", "Major Non-Compliance"] and is_empty(defect_image):
        errors.append("Defect Evidence Image is mandatory when logging Minor or Major Non-Compliance.")

    if work_stopped is True and is_empty(front_image):
        errors.append("Front-view Site Image is mandatory to document overall site condition when issuing a Stop Work order.")

    # --------------------------------------------------------
    # 8. Vertical Hierarchy & Construction Sequence Rules
    # --------------------------------------------------------
    activity = record.get("Construction Activity")
    level = record.get("Level / Floor")
    current_level_rank = LEVEL_HIERARCHY.get(level)

    if not plot_history.empty:
        # A. Find highest structural level previously executed on this plot
        structural_history = plot_history[
            plot_history["Construction Activity"].isin(STRUCTURAL_ACTIVITIES)
        ]

        highest_structural_rank = -1
        highest_structural_level_name = ""

        for _, past_row in structural_history.iterrows():
            past_level = past_row.get("Level / Floor")
            if past_level in LEVEL_HIERARCHY:
                past_rank = LEVEL_HIERARCHY[past_level]
                if past_rank > highest_structural_rank:
                    highest_structural_rank = past_rank
                    highest_structural_level_name = past_level

        # Rule 8.1: Structural Monotonic Ascent
        # Primary framing casting cannot move backwards down the structure
        superstructure_casting = ["Columns / Beams Casting", "Slab Casting"]
        if activity in superstructure_casting and current_level_rank is not None:
            if highest_structural_rank != -1 and current_level_rank < highest_structural_rank:
                errors.append(
                    f"Structural sequence violation: Cannot log '{activity}' on '{level}' "
                    f"(Rank {current_level_rank}) when '{highest_structural_level_name}' "
                    f"(Rank {highest_structural_rank}) has already been structurally reached."
                )

        # Rule 8.2: Finishing Trades Pre-requisite
        # Finishing trades cannot occur on a floor that has not been structurally cast yet
        if activity in FINISHING_ACTIVITIES and current_level_rank is not None:
            if highest_structural_rank != -1 and current_level_rank > highest_structural_rank:
                errors.append(
                    f"Construction sequence violation: Cannot log finishing trade '{activity}' on '{level}' "
                    f"before structural casting for that level has been logged (Current highest structural level: "
                    f"'{highest_structural_level_name}')."
                )

        # Rule 8.3: Physical Progress Non-Regression
        if progress_value is not None and "Progress %" in plot_history.columns:
            past_progresses = pd.to_numeric(plot_history["Progress %"], errors="coerce").dropna()
            if not past_progresses.empty:
                max_past_progress = past_progresses.max()
                if progress_value < max_past_progress:
                    errors.append(
                        f"Progress regression: Physical progress cannot drop from {max_past_progress:.1f}% "
                        f"to {progress_value:.1f}% without formal demolition/rework justification."
                    )

    return errors


print("🟢 validation.py loaded successfully.")