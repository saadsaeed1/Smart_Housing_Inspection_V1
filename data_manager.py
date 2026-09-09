
from pathlib import Path

import pandas as pd

from schema import INSPECTION_SCHEMA


# ------------------------------------------------------------
# Project Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path("/content/Smart_Housing_Inspection_V1")

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "inspection_data.csv"
)


# ------------------------------------------------------------
# Load Inspections
# ------------------------------------------------------------

def load_inspections():

    columns = list(INSPECTION_SCHEMA.keys())

    if DATA_FILE.exists():

        df = pd.read_csv(DATA_FILE)

        for column in columns:

            if column not in df.columns:
                df[column] = ""

        return df[columns]

    return pd.DataFrame(columns=columns)


# ------------------------------------------------------------
# Normalize Inspection Record
# ------------------------------------------------------------

def normalize_inspection(record):

    columns = list(INSPECTION_SCHEMA.keys())

    normalized = {}

    for column in columns:

        value = record.get(column, "")

        data_type = INSPECTION_SCHEMA[column]["data_type"]


        # ----------------------------------------------------
        # Empty / Missing Values
        # ----------------------------------------------------

        if value is None:

            normalized[column] = ""

            continue


        try:

            if pd.isna(value):

                normalized[column] = ""

                continue

        except (TypeError, ValueError):

            pass


        # ----------------------------------------------------
        # Strip Strings
        # ----------------------------------------------------

        if isinstance(value, str):

            value = value.strip()


        # ----------------------------------------------------
        # Empty String
        # ----------------------------------------------------

        if value == "":

            normalized[column] = ""

            continue


        # ----------------------------------------------------
        # Date
        # ----------------------------------------------------

        if data_type == "date":

            try:

                normalized[column] = (
                    pd.to_datetime(value)
                    .date()
                    .isoformat()
                )

            except (TypeError, ValueError):

                normalized[column] = ""


        # ----------------------------------------------------
        # Boolean
        # ----------------------------------------------------

        elif data_type == "boolean":

            if isinstance(value, bool):

                normalized[column] = value

            elif isinstance(value, str):

                value_lower = value.lower()

                if value_lower in [
                    "true",
                    "yes",
                    "1",
                ]:

                    normalized[column] = True

                elif value_lower in [
                    "false",
                    "no",
                    "0",
                ]:

                    normalized[column] = False

                else:

                    normalized[column] = ""

            elif isinstance(value, (int, float)):

                if value == 1:

                    normalized[column] = True

                elif value == 0:

                    normalized[column] = False

                else:

                    normalized[column] = ""

            else:

                normalized[column] = ""


        # ----------------------------------------------------
        # Float
        # ----------------------------------------------------

        elif data_type == "float":

            try:

                normalized[column] = float(value)

            except (TypeError, ValueError):

                normalized[column] = ""


        # ----------------------------------------------------
        # Image Path
        # ----------------------------------------------------

        elif data_type == "image_path":

            normalized[column] = str(value).strip()


        # ----------------------------------------------------
        # String
        # ----------------------------------------------------

        elif data_type == "string":

            normalized[column] = str(value).strip()


        # ----------------------------------------------------
        # Unknown Type
        # ----------------------------------------------------

        else:

            normalized[column] = value


    return normalized


# ------------------------------------------------------------
# Generate Inspection ID
# ------------------------------------------------------------

def generate_inspection_id(df):

    if df.empty:

        return "INS-001"


    existing_ids = (
        df["Inspection ID"]
        .dropna()
        .astype(str)
    )


    numbers = []


    for inspection_id in existing_ids:

        if inspection_id.startswith("INS-"):

            try:

                number = int(
                    inspection_id.replace(
                        "INS-",
                        ""
                    )
                )

                numbers.append(number)

            except ValueError:

                continue


    if not numbers:

        return "INS-001"


    next_number = max(numbers) + 1


    return f"INS-{next_number:03d}"


# ------------------------------------------------------------
# Add Inspection
# ------------------------------------------------------------

def add_inspection(record):

    df = load_inspections()

    record = normalize_inspection(record)

    record["Inspection ID"] = generate_inspection_id(df)

    columns = list(INSPECTION_SCHEMA.keys())


    new_record = {
        column: record.get(column, "")
        for column in columns
    }


    if df.empty:

        df = pd.DataFrame(
            [new_record],
            columns=columns
        )

    else:

        new_row = pd.DataFrame(
            [new_record],
            columns=columns
        )

        df = pd.concat(
            [df, new_row],
            ignore_index=True
        )


    DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    df.to_csv(
        DATA_FILE,
        index=False
    )


    return new_record


# ------------------------------------------------------------
# Get Inspections
# ------------------------------------------------------------

def get_inspections(
    column=None,
    value=None
):

    df = load_inspections()


    if column is None and value is None:

        return df


    if column not in df.columns:

        raise ValueError(
            f"Unknown column: {column}"
        )


    filtered_df = df[
        df[column].astype(str)
        == str(value)
    ].copy()


    return filtered_df


# ------------------------------------------------------------
# Update Inspection
# ------------------------------------------------------------

def update_inspection(
    inspection_id,
    updates
):

    df = load_inspections()


    matching_rows = df.index[
        df["Inspection ID"].astype(str)
        == str(inspection_id)
    ]


    if len(matching_rows) == 0:

        raise ValueError(
            f"Inspection ID not found: {inspection_id}"
        )


    if "Inspection ID" in updates:

        raise ValueError(
            "Inspection ID cannot be changed."
        )


    unknown_fields = [
        field
        for field in updates
        if field not in INSPECTION_SCHEMA
    ]


    if unknown_fields:

        raise ValueError(
            f"Unknown field(s): {unknown_fields}"
        )


    row_index = matching_rows[0]


    updates = normalize_inspection(updates)


    for field, value in updates.items():

        if field == "Inspection ID":
            continue

        df.at[row_index, field] = value


    df.to_csv(
        DATA_FILE,
        index=False
    )


    return df.loc[row_index].to_dict()


# ------------------------------------------------------------
# Delete Inspection
# ------------------------------------------------------------

def delete_inspection(inspection_id):

    df = load_inspections()


    matching_rows = df.index[
        df["Inspection ID"].astype(str)
        == str(inspection_id)
    ]


    if len(matching_rows) == 0:

        raise ValueError(
            f"Inspection ID not found: {inspection_id}"
        )


    df = df.drop(
        index=matching_rows[0]
    ).reset_index(drop=True)


    df.to_csv(
        DATA_FILE,
        index=False
    )


    return True


# ------------------------------------------------------------
# Module Verification
# ------------------------------------------------------------

print("🟢 data_manager.py loaded successfully.")
