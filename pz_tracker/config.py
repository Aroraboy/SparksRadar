"""Configuration for the P&Z Tracker tool."""

import os
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
LOG_FILE = BASE_DIR / "pz_tracker.log"

# Excel workbook that holds the city URLs *and* receives extracted data
EXCEL_FILE = BASE_DIR / "Cities_P_Z_Meeting_Info.xlsx"

# ---------------------------------------------------------------------------
# Keywords used to identify relevant agenda items
# ---------------------------------------------------------------------------
KEYWORDS: list[str] = [
    "rezoning",
    "preliminary plat",
    "final plat",
    "site plan",
    "planned development",
    "residential",
    "commercial",
    "industrial",
    "restaurant",
    "retail",
    "subdivision",
    "concept plan",
    "zoning change",
    "special use permit",
]

# ---------------------------------------------------------------------------
# Scraping behaviour
# ---------------------------------------------------------------------------
REQUEST_DELAY_SECONDS: float = 2.5          # polite delay between HTTP requests
PDF_DOWNLOAD_TIMEOUT: int = 60              # seconds
MAX_RETRIES: int = 3                        # retry count for downloads
PLAYWRIGHT_TIMEOUT: int = 30_000            # ms – Playwright page timeout

# ---------------------------------------------------------------------------
# Meeting‑date cutoff – only process agendas from this date onward
# ---------------------------------------------------------------------------
MIN_MEETING_DATE: date = date(2026, 2, 1)

_DATE_FORMATS = (
    "%B %d, %Y",   # February 17, 2026
    "%B %d %Y",    # February 17 2026
    "%b %d, %Y",   # Feb 17, 2026
    "%b %d %Y",    # Feb 17 2026
    "%m/%d/%Y",    # 02/17/2026
    "%Y-%m-%d",    # 2026-02-17
)


def is_meeting_date_recent(date_str: str) -> bool:
    """Return *True* if *date_str* is on or after ``MIN_MEETING_DATE``.

    Unknown / unparseable dates are allowed through (returns *True*).
    """
    if not date_str or date_str == "unknown":
        return True
    cleaned = date_str.strip().rstrip(",")
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return parsed >= MIN_MEETING_DATE
        except ValueError:
            continue
    return True  # can't parse → let it through


# ---------------------------------------------------------------------------
# Groq API (free tier – Llama 3)
# ---------------------------------------------------------------------------
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# City portal type → scraper mapping
# Each entry: city name → { "url": …, "portal_type": … }
# portal_type must match one of the scraper module names.
# ---------------------------------------------------------------------------
PORTAL_TYPE_CIVICPLUS = "civicplus"
PORTAL_TYPE_MUNICODE = "municode"
PORTAL_TYPE_CIVICCLERK = "civicclerk"
PORTAL_TYPE_CIVICWEB = "civicweb"
PORTAL_TYPE_LEGISTAR = "legistar"
PORTAL_TYPE_STANDARD_HTML = "standard_html"

# Default cities – this list is supplemented at runtime by the Excel file.
DEFAULT_CITIES: dict[str, dict] = {
    # ---- Already processed (original 5) ----
    "Lago Vista": {
        "url": "https://tx-lagovista.civicplus.com/368/Agendas-Minutes-After-April-2023",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Manor": {
        "url": "https://meetings.municode.com/PublishPage/index?cid=MANORTX&ppid=6e8791e4-3a6b-49c1-8f3f-03e061bae9d7&p=1",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    "Sherman": {
        "url": "https://www.ci.sherman.tx.us/701/Agendas-and-Minutes",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "SHERMANTX",
    },
    "Victoria": {
        "url": "https://victoriatx.civicweb.net/Portal/MeetingTypeList.aspx",
        "portal_type": PORTAL_TYPE_CIVICWEB,
    },
    "Elgin": {
        "url": "https://www.elgintexas.gov/129/Agendas-Minutes",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "elgintx",
    },
    # ---- CivicPlus cities ----
    "Cedar Park": {
        "url": "https://meetings.municode.com/PublishPage/index?cid=CPTX&ppid=aeca32f0-9f3d-4242-958a-5508adddf736&p=-1",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    "Leander": {
        "url": "https://leander.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Aubrey": {
        "url": "https://www.aubreytx.gov/AgendaCenter/Planning-Zoning-Commission-6",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Princeton": {
        "url": "https://princetontx.gov/AgendaCenter/Planning-Zoning-Commission-5",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Little Elm": {
        "url": "https://littleelm.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Oak Point": {
        "url": "https://www.oakpointtexas.com/AgendaCenter/Planning-Zoning-Commission-3",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Denison": {
        "url": "https://denisontx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "denisontx",
    },
    "Melissa": {
        "url": "https://www.cityofmelissa.com/AgendaCenter/Planning-Zoning-Commission-6",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Highland Village": {
        "url": "https://tx-highlandvillage2.civicplus.com/117/Agendas-Minutes",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Sanger": {
        "url": "https://sanger-tx.municodemeetings.com/",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    "Southlake": {
        "url": "https://www.cityofsouthlake.com/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Roanoke": {
        "url": "https://roanoketx.civicclerk.com/web/Home.aspx",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "roanoketx",
    },
    "Grapevine": {
        "url": "https://grapevine.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Quinlan": {
        "url": "https://tx-quinlan.civicplus.com/Archive.aspx?AMID=53",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Trophy Club": {
        "url": "https://trophyclubtx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "trophyclubtx",
    },
    "Kennedale": {
        "url": "https://kennedaletx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "kennedaletx",
    },
    "Alvarado": {
        "url": "https://alvaradotx.civicclerk.com/web/Home.aspx",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "alvaradotx",
    },
    "Balch Springs": {
        "url": "https://www.cityofbalchsprings.com/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Wilmer": {
        "url": "https://www.cityofwilmer.net/244/Agendas-Minutes",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Kaufman": {
        "url": "https://kaufmantx.civicclerk.com/web/home.aspx",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "kaufmantx",
    },
    "Argyle": {
        "url": "https://www.argyletx.com/AgendaCenter/Planning-Zoning-Commission-4",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Forney": {
        "url": "https://www.forneytx.gov/AgendaCenter/Planning-Zoning-Commission-5",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Fate": {
        "url": "https://www.fatetx.gov/AgendaCenter/Planning-Zoning-6",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Royse City": {
        "url": "https://www.roysecity.com/AgendaCenter/Planning-Zoning-6",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Crandall": {
        "url": "https://www.crandalltexas.com/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Cleburne": {
        "url": "https://www.cleburne.net/AgendaCenter/Planning-Zoning-Commission-15",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Mesquite": {
        "url": "https://www.cityofmesquite.com/AgendaCenter/Planning-Zoning-Commission-18/",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Midlothian": {
        "url": "https://www.midlothian.tx.us/Archive.aspx?AMID=32",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Rowlett": {
        "url": "https://www.rowletttx.gov/Archive.aspx?AMID=53",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Seagoville": {
        "url": "https://seagoville.us/Archive.aspx?AMID=36",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Ovilla": {
        "url": "https://www.cityofovilla.org/agendacenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Flower Mound": {
        "url": "https://flowermoundtx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "flowermoundtx",
    },
    "Plano": {
        "url": "https://plano.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    # ---- MuniCode cities ----
    "Prosper": {
        "url": "https://prosper-tx.municodemeetings.com/",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    "Burleson": {
        "url": "https://burleson-tx.municodemeetings.com/",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    "Joshua": {
        "url": "https://joshua-tx.municodemeetings.com/",
        "portal_type": PORTAL_TYPE_MUNICODE,
    },
    # ---- CivicClerk cities ----
    "Glenn Heights": {
        "url": "https://glennheightstx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "glennheightstx",
    },
    "Taylor": {
        "url": "https://www.ci.taylor.tx.us/18/Agendas-and-Minutes",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "taylortx",
    },
    # ---- CivicWeb cities ----
    "Terrell": {
        "url": "https://cityofterrell.civicweb.net/Portal/MeetingInformation.aspx?Id=11551",
        "portal_type": PORTAL_TYPE_CIVICWEB,
    },
    "Murphy": {
        "url": "https://murphytx.civicweb.net/Portal/",
        "portal_type": PORTAL_TYPE_CIVICWEB,
    },
    # ---- New CivicPlus AgendaCenter cities ----
    "Frisco": {
        "url": "https://www.friscotexas.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Gunter": {
        "url": "https://www.guntertx.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Anna": {
        "url": "https://www.annatexas.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "The Colony": {
        "url": "https://www.thecolonytx.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Lancaster": {
        "url": "https://www.lancaster-tx.com/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Liberty Hill": {
        "url": "https://www.libertyhilltx.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Cross Roads": {
        "url": "https://www.crossroadstx.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Cedar Hill": {
        "url": "https://tx-cedarhill4.civicplus.com/Archive.aspx?AMID=32",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Sunnyvale": {
        "url": "https://www.sunnyvaletx.org/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    "Corinth": {
        "url": "https://www.corinthtx.gov/AgendaCenter",
        "portal_type": PORTAL_TYPE_CIVICPLUS,
    },
    # ---- New CivicClerk cities ----
    "Belton": {
        "url": "https://beltontx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "beltontx",
    },
    "Addison": {
        "url": "https://addisontx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "addisontx",
    },
    "Duncanville": {
        "url": "https://duncanvilletx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "duncanvilletx",
    },
    "Crowley": {
        "url": "https://crowleytx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "crowleytx",
    },
    "Venus": {
        "url": "https://venustx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "venustx",
    },
    "Sachse": {
        "url": "https://sachsetx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "sachsetx",
    },
    "Josephine": {
        "url": "https://josephinetx.portal.civicclerk.com/",
        "portal_type": PORTAL_TYPE_CIVICCLERK,
        "api_subdomain": "josephinetx",
    },
    # ---- Legistar cities ----
    "Austin": {
        "url": "https://austin.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Carrollton": {
        "url": "https://carrollton.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Pflugerville": {
        "url": "https://pflugerville.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "McKinney": {
        "url": "https://mckinney.legistar.com/DepartmentDetail.aspx?ID=7094&GUID=00BF5AB6-E1DF-4966-A0F7-943ACCA0E1CF",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Lewisville": {
        "url": "https://cityoflewisville.legistar.com/DepartmentDetail.aspx?ID=40778&GUID=61C9A615-A2A5-46E2-885D-623D674E9898",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Denton": {
        "url": "https://denton.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Coppell": {
        "url": "https://coppell.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Keller": {
        "url": "https://cityofkeller.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Mansfield": {
        "url": "https://mansfield.legistar.com/Calendar.aspx?BodyID=16727",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Garland": {
        "url": "https://garland.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Arlington": {
        "url": "https://arlington.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Rockwall": {
        "url": "https://rockwall.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Richardson": {
        "url": "https://richardson.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
    "Grand Prairie": {
        "url": "https://gptx.legistar.com/Calendar.aspx",
        "portal_type": PORTAL_TYPE_LEGISTAR,
    },
}

# ---------------------------------------------------------------------------
# Excel column headers (must match the existing sheet layout)
# ---------------------------------------------------------------------------
EXCEL_COLUMNS: list[str] = [
    "CITIES",
    "P & Z DATE",
    "Owner name",
    "assigned general contractor",
    "architect",
    "APPLICANT NAME",
    "APPLICANT EMAIL",
    "APPLICANT PHONE NUMBER",
    "CONSTRUCTION TYPE",
    "LAND ACRES",
    "LOCATION",
    "DESCRIPTION OF THE APPILCATION PETITION",
    "URL",
]

# ---------------------------------------------------------------------------
# Email / scheduling
# ---------------------------------------------------------------------------
SCHEDULE_DAY: str = "monday"     # day of the week to run
SCHEDULE_TIME: str = "07:00"     # 24-hour format
