# ============================================================
# Smart Housing Inspection Dashboard V1
# Controlled Vocabulary & Site Configuration
# ============================================================

# Society Sectors
SECTORS = [
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "Overseas",
    "Commercial",
]

# Inspection Types
INSPECTION_TYPES = [
    "Routine Inspection",
    "Follow-up Inspection",
    "Complaint Inspection",
    "Pre-Construction Inspection",
    "Final Inspection",
    "Other",
]

# Vertical Levels & Monotonic Structural Hierarchy
LEVELS = [
    "Foundation / Sub-structure",
    "Basement",
    "Ground Floor",
    "First Floor",
    "Second Floor",
    "Rooftop / Parapet",
]

LEVEL_HIERARCHY = {
    "Foundation / Sub-structure": 0,
    "Basement": 1,
    "Ground Floor": 2,
    "First Floor": 3,
    "Second Floor": 4,
    "Rooftop / Parapet": 5,
}

# Trade Sequence Classifications
STRUCTURAL_ACTIVITIES = [
    "Excavation",
    "Foundation",
    "Rebar & Formwork Checking",
    "Columns / Beams Casting",
    "Slab Casting",
]

FINISHING_ACTIVITIES = [
    "Brickwork / Masonry",
    "Plastering",
    "MEP Rough-ins",
    "Flooring",
    "Painting",
    "Finishing",
]

CONSTRUCTION_ACTIVITIES = (
    STRUCTURAL_ACTIVITIES
    + FINISHING_ACTIVITIES
    + ["Boundary Wall", "Site Clearance", "Other"]
)

# Compliance & Enforcement Lists
COMPLIANCE_STATUSES = [
    "Compliant",
    "Minor Non-Compliance",
    "Major Non-Compliance",
]

SEVERITY_LEVELS = [
    "Low",
    "Medium",
    "High",
    "Critical",
]

VIOLATION_TYPES = [
    "No Violation",
    "DHA Byelaw",
    "Building Line / Setback",
    "Building Height",
    "Structural / Safety",
    "Construction Quality",
    "Approved Drawing Deviation",
    "Boundary / Site Issue",
    "Material / Workmanship",
    "Unauthorized Construction",
    "Other",
]