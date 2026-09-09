# ============================================================
# Smart Housing Inspection Dashboard V1
# Authoritative Inspection Schema
# ============================================================

# ------------------------------------------------------------
# Field definitions
#
# Each field contains:
# - label
# - data_type
# - required
# - conditional
# ------------------------------------------------------------

INSPECTION_SCHEMA = {
    "Inspection ID": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Inspection Date": {
        "data_type": "date",
        "required": True,
        "conditional": False,
    },

    "Inspector": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Sector": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Plot Number": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Owner": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Contractor": {
        "data_type": "string",
        "required": False,
        "conditional": False,
    },

    "Inspection Type": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Construction Activity": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Level / Floor": {
        "data_type": "string",
        "required": False,
        "conditional": True,
    },

    "Progress %": {
        "data_type": "float",
        "required": False,
        "conditional": False,
    },

    "Observation": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Defects": {
        "data_type": "string",
        "required": False,
        "conditional": True,
    },

    "Violation Type": {
        "data_type": "string",
        "required": False,
        "conditional": True,
    },

    "Severity": {
        "data_type": "string",
        "required": False,
        "conditional": True,
    },

    "Compliance Status": {
        "data_type": "string",
        "required": True,
        "conditional": False,
    },

    "Recommended Action": {
        "data_type": "string",
        "required": False,
        "conditional": True,
    },

    "Deadline": {
        "data_type": "date",
        "required": False,
        "conditional": True,
    },

    "Work Stopped": {
        "data_type": "boolean",
        "required": True,
        "conditional": False,
    },

    "Follow-up Required": {
        "data_type": "boolean",
        "required": True,
        "conditional": False,
    },

    "Follow-up Date": {
        "data_type": "date",
        "required": False,
        "conditional": True,
    },

    "Front-view Site Image": {
        "data_type": "image_path",
        "required": True,
        "conditional": False,
    },
}
