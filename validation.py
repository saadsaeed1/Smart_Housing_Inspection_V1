from pathlib import Path
from datetime import datetime
import pandas as pd
import config
from data_manager import load_inspections, normalize_plot_number


def validate_inspection(record: dict) -> list:
    """
    Validates an incoming or existing inspection record against civil engineering rules,
    statutory bylaws, and chronological non-regression constraints.
    Returns a list of error strings (empty list if valid).
    """
    errors = []

    # 1. Mandatory Fields
    required_fields = [
        "Inspection ID", "Inspection Date", "Inspector", "Sector",
        "Plot Number", "Owner", "Contractor", "Inspection Type",
        "Construction Activity", "Level / Floor", "Compliance Status"
    ]
    for field in required_fields:
        val = str(record.get(field, "")).strip()
        if not val or val in ["nan", "None"]:
            errors.append(f"Missing mandatory field: {field}")

    # 2. Enum Membership Checks
    if record.get("Inspection Type") not in config.INSPECTION_TYPES:
        errors.append(f"Inspection Type has an invalid value: {record.get('Inspection Type')}")

    if record.get("Construction Activity") not in config.CONSTRUCTION_ACTIVITIES:
        errors.append(f"Construction Activity has an invalid value: {record.get('Construction Activity')}")

    if record.get("Level / Floor") not in config.LEVELS:
        errors.append(f"Level / Floor has an invalid value: {record.get('Level / Floor')}")

    if record.get("Compliance Status") not in config.COMPLIANCE_STATUSES:
        errors.append(f"Compliance Status has an invalid value: {record.get('Compliance Status')}")

    v_type = record.get("Violation Type", "")
    if v_type and v_type not in config.VIOLATION_TYPES:
        errors.append(f"Violation Type has an invalid value: {v_type}")

    sev = record.get("Severity", "")
    if sev and sev not in config.SEVERITY_LEVELS:
        errors.append(f"Severity has an invalid value: {sev}")

    # 3. Date & Deadline Validation
    insp_date_str = str(record.get("Inspection Date", "")).strip()
    deadline_str = str(record.get("Deadline", "")).strip()

    parsed_insp_date = None
    if insp_date_str:
        try:
            parsed_insp_date = datetime.strptime(insp_date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Inspection Date format must be YYYY-MM-DD.")

    if deadline_str and deadline_str not in ["nan", "None"]:
        try:
            parsed_dl = datetime.strptime(deadline_str, "%Y-%m-%d").date()
            if parsed_insp_date and parsed_dl < parsed_insp_date:
                errors.append("Deadline cannot be before Inspection Date.")
        except ValueError:
            errors.append("Deadline format must be YYYY-MM-DD.")

    # 4. Photographic Evidence Mandate
    compliance = record.get("Compliance Status")
    front_img = str(record.get("Front-view Site Image", "")).strip()
    defect_img = str(record.get("Defect Evidence Image", "")).strip()

    if not front_img or front_img in ["nan", "None"]:
        errors.append("Front-view site image is mandatory for all inspections.")

    if compliance in ["Minor Non-Compliance", "Major Non-Compliance"]:
        if not defect_img or defect_img in ["nan", "None"]:
            errors.append("Forensic defect evidence image is mandatory for non-compliant inspections.")

    # 5. Monotonic Structural Ascent & Progress Non-Regression
    plot_num = normalize_plot_number(record.get("Plot Number", ""))
    incoming_id = str(record.get("Inspection ID", "")).strip()

    try:
        incoming_prog = float(str(record.get("Progress %", 0.0)).rstrip("%").strip())
    except ValueError:
        incoming_prog = 0.0

    if not (0.0 <= incoming_prog <= 100.0):
        errors.append("Progress % must be between 0.0 and 100.0.")

    # Historical verification against prior records
    df = load_inspections()
    if not df.empty and plot_num and parsed_insp_date:
        plot_df = df[df["Plot Number"].astype(str) == plot_num].copy()
        
        # Exclude the exact record being evaluated/edited
        if incoming_id and "Inspection ID" in plot_df.columns:
            plot_df = plot_df[plot_df["Inspection ID"].astype(str) != incoming_id]

        if not plot_df.empty:
            plot_df["Parsed_Historical_Date"] = pd.to_datetime(plot_df["Inspection Date"], errors="coerce").dt.date
            
            # Filter strictly to chronologically prior visits
            prior_visits = plot_df[plot_df["Parsed_Historical_Date"] < parsed_insp_date]
            
            if not prior_visits.empty:
                prior_progs = pd.to_numeric(
                    prior_visits["Progress %"].astype(str).str.rstrip("%"), errors="coerce"
                ).dropna()
                
                if not prior_progs.empty:
                    max_prior_prog = prior_progs.max()
                    if incoming_prog < max_prior_prog:
                        errors.append(
                            f"Progress regression: Physical progress cannot drop from {max_prior_prog}% to {incoming_prog}% without formal demolition/rework justification."
                        )

    return errors