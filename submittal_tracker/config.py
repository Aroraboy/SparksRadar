"""Configuration for the Submittal Tracker tool."""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"

# ---------------------------------------------------------------------------
# Google Sheets
# ---------------------------------------------------------------------------
# Will be set per-run; can also be overridden via env / CLI
SPREADSHEET_ID: str = ""

SHEET_COLUMNS: list[str] = [
    "Project Name",
    "Case Number",
    "Type",
    "Address",
    "Description",
    "Status",
    "Submittal Date",
    "Notes",
    "Source File",
    "Lead Priority",
]

# ---------------------------------------------------------------------------
# Archive source configuration  (one entry per city)
# ---------------------------------------------------------------------------
CITIES: dict[str, dict] = {
    "Frisco": {
        "archive_url": "https://www.friscotexas.gov/Archive.aspx?AMID=81",
        "base_url": "https://www.friscotexas.gov",
        "pdf_url_template": "https://www.friscotexas.gov/ArchiveCenter/ViewFile/Item/{adid}",
    },
}

# ---------------------------------------------------------------------------
# Project-number prefix → human-readable type
# ---------------------------------------------------------------------------
PROJECT_TYPE_MAP: dict[str, str] = {
    "CP":  "Commercial Plan",
    "FP":  "Final Plat",
    "SP":  "Site Plan",
    "PSP": "Preliminary Site Plan",
    "PP":  "Preliminary Plat",
    "RP":  "Replat",
    "MP":  "Minor Plat",
    "ZC":  "Zoning Change",
    "SUP": "Specific Use Permit",
    "CUP": "Conditional Use Permit",
    "VAR": "Variance",
    "AP":  "Amending Plat",
    "MDP": "Master Development Plan",
    "DP":  "Development Plan",
    "LP":  "Landscape Plan",
}

# ---------------------------------------------------------------------------
# Lead-priority keyword rules
# ---------------------------------------------------------------------------
HIGH_PRIORITY_KEYWORDS: list[str] = [
    "warehouse", "distribution center", "office building",
    "mixed use", "mixed-use", "hospital", "medical center",
    "hotel", "apartment", "multifamily", "multi-family",
    "shopping center", "retail center", "commercial",
    "industrial", "manufacturing",
]

MEDIUM_PRIORITY_KEYWORDS: list[str] = [
    "restaurant", "retail", "office", "church",
    "school", "daycare", "day care", "clinic",
    "garage", "parking", "gas station", "fuel",
    "car wash", "storage", "self-storage",
    "assisted living", "senior living",
]
