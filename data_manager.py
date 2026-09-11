import os
import re
from datetime import datetime
from pathlib import Path
import pandas as pd

from schema import INSPECTION_SCHEMA

# Dynamic Root Resolution (Works both in Colab and local environments)
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
SITE_IMAGES_DIR = ASSETS_DIR / "site_images"
DATA_FILE = DATA_DIR / "inspection_data.csv"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
SITE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def normalize_plot_number(raw_plot):
    """Standardizes plot strings: ' 40 / b ' -> '40-B'"""
    if not raw_plot or pd.isna(raw_plot):
        return ""
    plot = str(raw_plot).strip().upper()
    return re.sub(r"[\s/_]+", "-", plot)


def save_evidence_image(uploaded_file, plot_number, image_type="front"):
    """
    Saves an uploaded image with an immutable, timestamped filename.
    Format: {PLOT}_{YYYYMMDD_HHMMSS}_{TYPE}_{CLEAN_NAME}
    """
    if uploaded_file is None:
        return ""

    safe_plot = normalize_plot_number(plot_number)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_original_name = re.sub(r"[^\w\.-]", "_", uploaded_file.name)

    filename = f"{safe_plot}_{timestamp}_{image_type}_{clean_original_name}"
    target_path = SITE_IMAGES_DIR / filename

    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return f"assets/site_images/{filename}"


def load_inspections():
    columns = list(INSPECTION_SCHEMA.keys())
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE)
            for col in columns:
                if col not in df.columns:
                    df[col] = ""
            return df[columns]
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)


def normalize_inspection(record):
    columns = list(INSPECTION_SCHEMA.keys())
    normalized = {}

    for column in columns:
        value = record.get(column, "")
        data_type = INSPECTION_SCHEMA[column]["data_type"]

        if value is None:
            normalized[column] = ""
            continue

        try:
            if pd.isna(value):
                normalized[column] = ""
                continue
        except (TypeError, ValueError):
            pass

        if isinstance(value, str):
            value = value.strip()

        if value == "":
            normalized[column] = ""
            continue

        if data_type == "date":
            try:
                normalized[column] = pd.to_datetime(value).date().isoformat()
            except (TypeError, ValueError):
                normalized[column] = ""

        elif data_type == "boolean":
            if isinstance(value, bool):
                normalized[column] = value
            elif isinstance(value, str):
                val_lower = value.lower()
                if val_lower in ["true", "yes", "1"]:
                    normalized[column] = True
                elif val_lower in ["false", "no", "0"]:
                    normalized[column] = False
                else:
                    normalized[column] = ""
            elif isinstance(value, (int, float)):
                normalized[column] = True if value == 1 else (False if value == 0 else "")
            else:
                normalized[column] = ""

        elif data_type == "float":
            try:
                normalized[column] = float(value)
            except (TypeError, ValueError):
                normalized[column] = ""

        elif data_type in ["image_path", "string"]:
            normalized[column] = str(value).strip()

        else:
            normalized[column] = value

    # Automatically clean plot identifier
    if "Plot Number" in normalized and normalized["Plot Number"]:
        normalized["Plot Number"] = normalize_plot_number(normalized["Plot Number"])

    return normalized


def generate_inspection_id(df):
    if df.empty or "Inspection ID" not in df.columns or df["Inspection ID"].dropna().empty:
        return "INS-001"

    existing_ids = df["Inspection ID"].dropna().astype(str)
    numbers = []

    for insp_id in existing_ids:
        if insp_id.startswith("INS-"):
            try:
                numbers.append(int(insp_id.replace("INS-", "")))
            except ValueError:
                continue

    if not numbers:
        return "INS-001"

    return f"INS-{max(numbers) + 1:03d}"


def add_inspection(record):
    df = load_inspections()
    record = normalize_inspection(record)
    record["Inspection ID"] = generate_inspection_id(df)

    columns = list(INSPECTION_SCHEMA.keys())
    new_record = {col: record.get(col, "") for col in columns}
    new_row = pd.DataFrame([new_record], columns=columns)

    if df.empty:
        df = new_row
    else:
        df = pd.concat([df, new_row], ignore_index=True)

    df.to_csv(DATA_FILE, index=False)
    return new_record


def get_inspections(column=None, value=None):
    df = load_inspections()
    if column is None and value is None:
        return df
    if column not in df.columns:
        raise ValueError(f"Unknown column: {column}")
    return df[df[column].astype(str) == str(value)].copy()