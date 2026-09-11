# ============================================================
# Smart Housing Inspection Dashboard V1
# Authoritative Inspection Schema (23 Fields)
# ============================================================

INSPECTION_SCHEMA = {
    # System Metadata
    "Inspection ID": {
        "data_type": "string",
        "required": False,  # Auto-generated downstream by data_manager
        "conditional": False,
        "description": "Unique inspection identifier (e.g. INS-001)",
    },

    # Inspection Context
    "Inspection Date": {
        "data_type": "date",
        "required": True,
        "conditional": False,
        "description": "Date the site visit took place",
    },
    "Inspector": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Full name of the inspecting engineer",
    },
    "Sector": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Housing society sector or zone",
    },
    "Plot Number": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Standardized plot identifier (e.g. 40-B)",
    },
    "Owner": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Property owner or allottee name",
    },
    "Contractor": {
        "data_type": "string",
        "required": False,
        "conditional": False,
        "description": "Contractor or builder executing the work",
    },
    "Inspection Type": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Routine, Milestone, Re-inspection, etc.",
    },

    # Construction Progress
    "Construction Activity": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Current on-site active trade/stage",
    },
    "Level / Floor": {
        "data_type": "string",
        "required": False,
        "conditional": True,
        "description": "Vertical location of inspected work",
    },
    "Progress %": {
        "data_type": "float",
        "required": False,
        "conditional": False,
        "description": "Estimated site physical progress (0 - 100%)",
    },

    # Observations & Compliance
    "Observation": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Engineering notes and description of work observed",
    },
    "Defects": {
        "data_type": "string",
        "required": False,
        "conditional": True,
        "description": "Specific structural or finishing defects logged",
    },
    "Compliance Status": {
        "data_type": "string",
        "required": True,
        "conditional": False,
        "description": "Compliant, Minor Non-Compliance, Major Non-Compliance",
    },
    "Violation Type": {
        "data_type": "string",
        "required": False,
        "conditional": True,
        "description": "Category of building by-law or safety violation",
    },
    "Severity": {
        "data_type": "string",
        "required": False,
        "conditional": True,
        "description": "Low, Medium, High, Critical",
    },
    "Recommended Action": {
        "data_type": "string",
        "required": False,
        "conditional": True,
        "description": "Required corrective measures for the contractor",
    },

    # Enforcement & Scheduling
    "Work Stopped": {
        "data_type": "boolean",
        "required": True,
        "conditional": False,
        "description": "Formal stop-work order issued on plot",
    },
    "Deadline": {
        "data_type": "date",
        "required": False,
        "conditional": True,
        "description": "Rectification deadline given to builder",
    },
    "Follow-up Required": {
        "data_type": "boolean",
        "required": True,
        "conditional": False,
        "description": "Flag requiring a subsequent site visit",
    },
    "Follow-up Date": {
        "data_type": "date",
        "required": False,
        "conditional": True,
        "description": "Target date for subsequent verification inspection",
    },

    # Dual Photographic Evidence
    "Front-view Site Image": {
        "data_type": "image_path",
        "required": False,  # Handled dynamically by validation.py
        "conditional": True,
        "description": "Macro street-elevation photo establishing site progress and presence",
    },
    "Defect Evidence Image": {
        "data_type": "image_path",
        "required": False,  # Handled dynamically by validation.py
        "conditional": True,
        "description": "Micro close-up photo substantiating violations or stop-work orders",
    },
}