"""Run the full pipeline for all new cities that have working scrapers."""
import asyncio
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.FileHandler("pz_tracker.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pz_pipeline")

from config import DEFAULT_CITIES, DOWNLOAD_DIR, EXCEL_FILE, REQUEST_DELAY_SECONDS, is_meeting_date_recent
from scrapers.base_scraper import AgendaResult
from scrapers.civicclerk import CivicClerkScraper
from scrapers.civicplus import CivicPlusScraper
from scrapers.civicweb import CivicWebScraper
from scrapers.municode import MuniCodeScraper
from scrapers.standard_html import StandardHtmlScraper
from scrapers.legistar import LegistarScraper
from parsers.ai_extractor import extract_from_text
from parsers.pdf_parser import extract_full_text, parse_agenda
from utils.downloader import download_pdf
from writers.excel_writer import write_records, write_no_data_record
from writers.google_sheets_writer import write_records_to_sheets, write_no_data_to_sheets

SCRAPER_MAP = {
    "civicplus": CivicPlusScraper,
    "municode": MuniCodeScraper,
    "civicclerk": CivicClerkScraper,
    "civicweb": CivicWebScraper,
    "legistar": LegistarScraper,
    "standard_html": StandardHtmlScraper,
}

# Skip cities that already have data
ALREADY_DONE = {
    "Lago Vista", "Manor", "Sherman", "Victoria", "Elgin",
    "Glenn Heights", "Taylor", "Terrell",
    "Cedar Park", "Aubrey", "Princeton", "Oak Point", "Sanger", "Southlake",
    "Highland Village", "Quinlan", "Argyle", "Forney", "Fate",
    "Cleburne", "Mesquite", "Midlothian",
    "Roanoke", "Prosper", "Burleson", "Joshua", "Venus",
    "Cross Roads", "Crowley", "Duncanville",
    "Denison", "Flower Mound", "Keller", "Kennedale", "Lewisville", "Trophy Club",
    # Phase 1 done (no data)
    "Alvarado", "Kaufman", "Sachse",
    # Phase 2 done
    "Melissa", "Balch Springs", "Wilmer", "Royse City", "Crandall",
    "Rowlett", "Seagoville", "Ovilla", "Frisco", "Gunter", "Anna",
    "The Colony", "Lancaster", "Liberty Hill", "Cedar Hill",
    "Sunnyvale", "Corinth",
    # Phase 2 no-data (backfilled)
    "Leander", "Little Elm", "Grapevine",
}
KNOWN_FAILS = {"Belton", "Addison", "Josephine"}  # CivicClerk API 404, portals non-functional

# ── Phase control ──────────────────────────────────────────────────
# Set CURRENT_PHASE to run only cities of a particular portal type.
# Set to None to run all pending cities.
CURRENT_PHASE = "legistar"  # Phase 3


async def scrape_city(city, info):
    from playwright.async_api import async_playwright
    portal_type = info.get("portal_type", "standard_html")
    scraper_cls = SCRAPER_MAP.get(portal_type)
    if not scraper_cls:
        return None

    kwargs = {"city": city, "url": info["url"]}
    if portal_type == "civicclerk" and info.get("api_subdomain"):
        kwargs["api_subdomain"] = info["api_subdomain"]

    scraper = scraper_cls(**kwargs)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            return await scraper.find_latest_agenda(page)
        except Exception:
            logger.exception("Scraper error for %s", city)
            return None
        finally:
            await browser.close()


def process_agenda(agenda):
    city = agenda.city
    city_dir = DOWNLOAD_DIR / city.replace(" ", "_")
    city_dir.mkdir(parents=True, exist_ok=True)

    agenda_path = download_pdf(agenda.pdf_url, dest_dir=city_dir, filename="agenda.pdf")
    if not agenda_path:
        logger.error("Failed to download agenda for %s", city)
        return []

    # Skip excessively large PDFs (>50 MB) that hang pdfplumber
    pdf_size_mb = agenda_path.stat().st_size / (1024 * 1024)
    if pdf_size_mb > 50:
        logger.warning("PDF too large (%.0f MB) for %s – skipping parse", pdf_size_mb, city)
        return []

    items = parse_agenda(agenda_path)
    if not items:
        logger.info("No relevant items in agenda for %s", city)
        return []

    all_records = []
    seen_urls = set()
    secondary_urls = []
    for item in items:
        for url in item.linked_urls:
            if url.lower().endswith(".pdf") and url not in seen_urls:
                seen_urls.add(url)
                secondary_urls.append((url, item.text[:120]))

    if secondary_urls:
        logger.info("Found %d secondary PDF(s) for %s", len(secondary_urls), city)
        for idx, (sec_url, label) in enumerate(secondary_urls, start=1):
            time.sleep(REQUEST_DELAY_SECONDS)
            sec_path = download_pdf(sec_url, dest_dir=city_dir, filename=f"detail_{idx}.pdf")
            if not sec_path:
                continue
            pdf_text = extract_full_text(sec_path)
            if not pdf_text.strip():
                continue
            records = extract_from_text(pdf_text, city=city, meeting_date=agenda.meeting_date)
            for rec in records:
                rec.setdefault("url", agenda.pdf_url)
            all_records.extend(records)
    else:
        logger.info("No secondary PDFs; extracting from main agenda for %s", city)
        pdf_text = extract_full_text(agenda_path)
        records = extract_from_text(pdf_text, city=city, meeting_date=agenda.meeting_date)
        for rec in records:
            rec.setdefault("url", agenda.pdf_url)
        all_records.extend(records)

    return all_records


def _record_no_data(city: str, info: dict, reason: str) -> None:
    """Record a city with no relevant data in both Excel and Google Sheets."""
    portal_type = info.get("portal_type", "")
    try:
        write_no_data_record(city, reason=reason, excel_path=EXCEL_FILE)
    except Exception:
        logger.exception("Failed to write no-data Excel row for %s", city)
    try:
        write_no_data_to_sheets(city, portal_type=portal_type, reason=reason)
    except Exception:
        logger.exception("Failed to write no-data Google Sheets row for %s", city)


def main():
    cities_to_run = {
        k: v for k, v in DEFAULT_CITIES.items()
        if k not in ALREADY_DONE and k not in KNOWN_FAILS
    }

    # Phase filter
    if CURRENT_PHASE:
        cities_to_run = {k: v for k, v in cities_to_run.items()
                         if v.get("portal_type") == CURRENT_PHASE}

    print(f"Running pipeline for {len(cities_to_run)} cities (phase={CURRENT_PHASE or 'all'})")
    summary = {}

    for city, info in cities_to_run.items():
        logger.info("=" * 60)
        logger.info("Processing: %s", city)
        logger.info("=" * 60)

        try:
            agenda = asyncio.run(scrape_city(city, info))
        except Exception:
            logger.exception("Failed to scrape %s", city)
            _record_no_data(city, info, "No relevant data found – scraper error")
            summary[city] = 0
            continue

        if not agenda:
            logger.warning("No agenda found for %s", city)
            _record_no_data(city, info, "No relevant data found – no agenda located")
            summary[city] = 0
            continue

        if not is_meeting_date_recent(agenda.meeting_date):
            logger.info(
                "Agenda for %s is too old (%s) – skipping", city, agenda.meeting_date
            )
            _record_no_data(city, info, f"No relevant data found – latest agenda too old ({agenda.meeting_date})")
            summary[city] = 0
            continue

        records = process_agenda(agenda)
        if not records:
            logger.info("No records extracted for %s", city)
            _record_no_data(city, info, "No relevant data found – agenda had no matching items")
            summary[city] = 0
            continue

        written = write_records(records, city=city, excel_path=EXCEL_FILE)

        try:
            portal_type = info.get("portal_type", "")
            gs_written = write_records_to_sheets(records, city=city, portal_type=portal_type)
            logger.info("Google Sheets: %d record(s) for %s", gs_written, city)
        except Exception:
            logger.exception("Failed to write to Google Sheets for %s", city)

        summary[city] = written
        time.sleep(REQUEST_DELAY_SECONDS)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    total = 0
    for city, count in summary.items():
        icon = "✓" if count > 0 else "✗"
        print(f"  {icon} {city}: {count} record(s)")
        total += count
    print(f"\nTotal: {total} records from {len(summary)} cities")


if __name__ == "__main__":
    main()
