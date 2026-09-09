
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
    # Required Fields
    # --------------------------------------------------------
    # Inspection ID is excluded because it is generated
    # automatically by data_manager.add_inspection().
    # --------------------------------------------------------

    for field, rules in INSPECTION_SCHEMA.items():

        if field == "Inspection ID":
            continue

        if not rules["required"]:
            continue

        value = record.get(field)

        if is_empty(value):

            errors.append(
                f"{field} is required."
            )


    # --------------------------------------------------------
    # Controlled Values
    # --------------------------------------------------------

    for field, allowed_values in CONTROLLED_VALUES.items():

        value = record.get(field)

        if is_empty(value):
            continue

        if value not in allowed_values:

            errors.append(
                f"{field} has an invalid value: {value}"
            )


    # --------------------------------------------------------
    # Progress %
    # --------------------------------------------------------

    progress = record.get("Progress %")

    if not is_empty(progress):

        try:

            progress_value = float(progress)

            if progress_value < 0 or progress_value > 100:

                errors.append(
                    "Progress % must be between 0 and 100."
                )

        except (TypeError, ValueError):

            errors.append(
                "Progress % must be a numeric value "
                "between 0 and 100."
            )


    # --------------------------------------------------------
    # Compliance Rules
    # --------------------------------------------------------

    compliance_status = record.get(
        "Compliance Status"
    )

    violation_type = record.get(
        "Violation Type"
    )

    severity = record.get(
        "Severity"
    )

    recommended_action = record.get(
        "Recommended Action"
    )


    if compliance_status == "Compliant":

        if violation_type != "No Violation":

            errors.append(
                "For a Compliant inspection, "
                "Violation Type must be 'No Violation'."
            )

        if not is_empty(severity):

            errors.append(
                "Severity should be empty for "
                "a Compliant inspection."
            )


    elif compliance_status in [
        "Minor Non-Compliance",
        "Major Non-Compliance",
    ]:

        if is_empty(violation_type):

            errors.append(
                "Violation Type is required for "
                "a non-compliant inspection."
            )

        elif violation_type == "No Violation":

            errors.append(
                "A non-compliant inspection cannot have "
                "'No Violation' as the Violation Type."
            )


        if is_empty(severity):

            errors.append(
                "Severity is required for "
                "a non-compliant inspection."
            )


        if is_empty(recommended_action):

            errors.append(
                "Recommended Action is required for "
                "a non-compliant inspection."
            )


    # --------------------------------------------------------
    # Work Stopped Rules
    # --------------------------------------------------------

    work_stopped = record.get(
        "Work Stopped"
    )


    if work_stopped is True:

        if compliance_status == "Compliant":

            errors.append(
                "Work Stopped cannot be Yes "
                "for a Compliant inspection."
            )


        if is_empty(violation_type):

            errors.append(
                "Violation Type is required when "
                "Work Stopped is Yes."
            )

        elif violation_type == "No Violation":

            errors.append(
                "Work Stopped cannot be Yes when "
                "Violation Type is 'No Violation'."
            )


        if is_empty(severity):

            errors.append(
                "Severity is required when "
                "Work Stopped is Yes."
            )


        if is_empty(recommended_action):

            errors.append(
                "Recommended Action is required when "
                "Work Stopped is Yes."
            )


    # --------------------------------------------------------
    # Follow-up Rules
    # --------------------------------------------------------

    follow_up_required = record.get(
        "Follow-up Required"
    )

    follow_up_date = record.get(
        "Follow-up Date"
    )

    inspection_date = record.get(
        "Inspection Date"
    )


    if follow_up_required is True:

        if is_empty(follow_up_date):

            errors.append(
                "Follow-up Date is required when "
                "Follow-up Required is Yes."
            )


    elif follow_up_required is False:

        if not is_empty(follow_up_date):

            errors.append(
                "Follow-up Date should be empty when "
                "Follow-up Required is No."
            )


    # --------------------------------------------------------
    # Follow-up Date Rule
    # --------------------------------------------------------

    if (
        not is_empty(follow_up_date)
        and not is_empty(inspection_date)
    ):

        try:

            inspection_date_value = (
                pd.to_datetime(
                    inspection_date
                ).date()
            )

            follow_up_date_value = (
                pd.to_datetime(
                    follow_up_date
                ).date()
            )


            if (
                follow_up_date_value
                < inspection_date_value
            ):

                errors.append(
                    "Follow-up Date cannot be before "
                    "Inspection Date."
                )

        except (TypeError, ValueError):

            pass


    # --------------------------------------------------------
    # Deadline Rules
    # --------------------------------------------------------

    deadline = record.get(
        "Deadline"
    )


    if compliance_status in [
        "Minor Non-Compliance",
        "Major Non-Compliance",
    ]:

        if is_empty(deadline):

            errors.append(
                "Deadline is required for "
                "a non-compliant inspection."
            )


    if work_stopped is True:

        if is_empty(deadline):

            errors.append(
                "Deadline is required when "
                "Work Stopped is Yes."
            )


    # --------------------------------------------------------
    # Deadline Date Rule
    # --------------------------------------------------------

    if (
        not is_empty(deadline)
        and not is_empty(inspection_date)
    ):

        try:

            inspection_date_value = (
                pd.to_datetime(
                    inspection_date
                ).date()
            )

            deadline_value = (
                pd.to_datetime(
                    deadline
                ).date()
            )


            if deadline_value < inspection_date_value:

                errors.append(
                    "Deadline cannot be before "
                    "Inspection Date."
                )

        except (TypeError, ValueError):

            pass


    return errors


print("🟢 validation.py loaded successfully.")
