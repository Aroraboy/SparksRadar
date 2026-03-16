"""P&Z Tracker – main entry point.

Orchestrates the full pipeline:
  1. Load city list from config / Excel
  2. For each city, scrape the portal for the latest agenda PDF
  3. Download and parse the agenda for relevant items
  4. Download secondary PDFs linked from agenda items
  5. Extract structured data via Claude API
  6. Write results to Excel
  7. Optionally send an email summary
"""

from __future__ import annotations

import asyncio
import logging
import os
import smtplib
import sys
import time
from email.mime.text import MIMEText
from pathlib import Path

import schedule
from dotenv import load_dotenv

# Ensure the project root is on sys.path so relative imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import (
    DEFAULT_CITIES,
    DOWNLOAD_DIR,
    EXCEL_FILE,
    LOG_FILE,
    REQUEST_DELAY_SECONDS,
    SCHEDULE_DAY,
    SCHEDULE_TIME,
    is_meeting_date_recent,
)
from parsers.ai_extractor import extract_from_text
from parsers.pdf_parser import extract_full_text, parse_agenda
from scrapers.base_scraper import AgendaResult
from scrapers.civicclerk import CivicClerkScraper
from scrapers.civicplus import CivicPlusScraper
from scrapers.civicweb import CivicWebScraper
from scrapers.municode import MuniCodeScraper
from scrapers.standard_html import StandardHtmlScraper
from utils.downloader import download_pdf
from writers.excel_writer import write_records
from writers.google_sheets_writer import write_records_to_sheets, copy_excel_to_sheets

load_dotenv()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pz_tracker")

# ---------------------------------------------------------------------------
# Scraper registry
# ---------------------------------------------------------------------------
SCRAPER_MAP = {
    "civicplus": CivicPlusScraper,
    "municode": MuniCodeScraper,
    "civicclerk": CivicClerkScraper,
    "civicweb": CivicWebScraper,
    "standard_html": StandardHtmlScraper,
}


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

async def _scrape_city(city: str, info: dict) -> AgendaResult | None:
    """Launch Playwright, scrape a single city, return an AgendaResult."""
    from playwright.async_api import async_playwright

    portal_type = info.get("portal_type", "standard_html")
    scraper_cls = SCRAPER_MAP.get(portal_type)
    if scraper_cls is None:
        logger.error("Unknown portal type '%s' for %s – skipping", portal_type, city)
        return None

    scraper_kwargs = {"city": city, "url": info["url"]}
    if portal_type == "civicclerk" and info.get("api_subdomain"):
        scraper_kwargs["api_subdomain"] = info["api_subdomain"]
    scraper = scraper_cls(**scraper_kwargs)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not info.get("headed", False))
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        try:
            result = await scraper.find_latest_agenda(page)
        except Exception:
            logger.exception("Scraper error for %s", city)
            result = None
        finally:
            await browser.close()

    return result


def _process_agenda(agenda: AgendaResult) -> list[dict]:
    """Download agenda PDF, parse it, download secondary PDFs, run AI extraction."""
    city = agenda.city
    city_dir = DOWNLOAD_DIR / city.replace(" ", "_")
    city_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download main agenda PDF
    agenda_path = download_pdf(agenda.pdf_url, dest_dir=city_dir, filename="agenda.pdf")
    if agenda_path is None:
        logger.error("Failed to download agenda PDF for %s", city)
        return []

    # 2. Parse agenda for relevant items
    items = parse_agenda(agenda_path)
    if not items:
        logger.info("No relevant items in agenda for %s", city)
        return []

    all_records: list[dict] = []

    # 3. Collect unique secondary PDF URLs from agenda items
    seen_urls: set[str] = set()
    secondary_urls: list[tuple[str, str]] = []  # (url, item_text_snippet)
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
            if sec_path is None:
                logger.warning("Could not download secondary PDF: %s", sec_url)
                continue

            pdf_text = extract_full_text(sec_path)
            if not pdf_text.strip():
                logger.warning("Secondary PDF is empty/unreadable: %s", sec_path)
                continue

            records = extract_from_text(pdf_text, city=city, meeting_date=agenda.meeting_date)
            for rec in records:
                # Always link to the full Agenda Packet, not sub-documents
                rec.setdefault("url", agenda.pdf_url)
                rec.setdefault("status", "New")
            all_records.extend(records)
    else:
        # No secondary PDFs – extract from the main agenda itself
        logger.info("No secondary PDFs; extracting from main agenda for %s", city)
        pdf_text = extract_full_text(agenda_path)
        records = extract_from_text(pdf_text, city=city, meeting_date=agenda.meeting_date)
        for rec in records:
            rec.setdefault("url", agenda.pdf_url)
            rec.setdefault("status", "New")
        all_records.extend(records)

    return all_records


def run_pipeline(cities: dict[str, dict] | None = None, headed: bool = False) -> dict[str, int]:
    """Run the full pipeline for all cities. Returns {city: rows_written}."""
    cities = cities or DEFAULT_CITIES
    summary: dict[str, int] = {}

    for city, info in cities.items():
        logger.info("=" * 60)
        logger.info("Processing: %s", city)
        logger.info("=" * 60)

        try:
            if headed:
                info = {**info, "headed": True}
            agenda = asyncio.run(_scrape_city(city, info))
        except Exception:
            logger.exception("Failed to scrape %s", city)
            summary[city] = 0
            continue

        if agenda is None:
            logger.warning("No agenda found for %s – skipping", city)
            summary[city] = 0
            continue

        if not is_meeting_date_recent(agenda.meeting_date):
            logger.info(
                "Agenda for %s is too old (%s) – skipping", city, agenda.meeting_date
            )
            summary[city] = 0
            continue

        records = _process_agenda(agenda)
        if not records:
            logger.info("No records extracted for %s", city)
            summary[city] = 0
            continue

        written = write_records(records, city=city, excel_path=EXCEL_FILE)

        # Also write to Google Sheets
        try:
            portal_type = info.get("portal_type", "")
            gs_written = write_records_to_sheets(records, city=city, portal_type=portal_type)
            logger.info("Google Sheets: %d record(s) for %s", gs_written, city)
        except Exception:
            logger.exception("Failed to write to Google Sheets for %s", city)

        summary[city] = written

        # polite delay before hitting the next city
        time.sleep(REQUEST_DELAY_SECONDS)

    return summary


# ---------------------------------------------------------------------------
# Email summary
# ---------------------------------------------------------------------------

def send_email_summary(summary: dict[str, int]) -> None:
    """Send a plain-text email with the run results."""
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([sender, password, recipient]):
        logger.info("Email credentials not configured – skipping email summary")
        return

    lines = ["P&Z Tracker – Weekly Run Summary", "=" * 40, ""]
    total = 0
    for city, count in summary.items():
        lines.append(f"  {city}: {count} new record(s)")
        total += count
    lines.append("")
    lines.append(f"Total new records: {total}")

    body = "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = f"P&Z Tracker: {total} new record(s) found"
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, [recipient], msg.as_string())
        logger.info("Email summary sent to %s", recipient)
    except Exception:
        logger.exception("Failed to send email summary")


# ---------------------------------------------------------------------------
# Scheduled mode
# ---------------------------------------------------------------------------

def run_scheduled() -> None:
    """Block forever, running the pipeline on the configured schedule."""
    logger.info("Scheduling weekly run: every %s at %s", SCHEDULE_DAY, SCHEDULE_TIME)
    getattr(schedule.every(), SCHEDULE_DAY).at(SCHEDULE_TIME).do(_scheduled_job)

    # Also run once immediately
    _scheduled_job()

    while True:
        schedule.run_pending()
        time.sleep(60)


def _scheduled_job() -> None:
    logger.info("Scheduled job triggered")
    summary = run_pipeline()
    send_email_summary(summary)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="P&Z Meeting Tracker")
    parser.add_argument(
        "--schedule", action="store_true",
        help="Run on a weekly schedule instead of once",
    )
    parser.add_argument(
        "--city", type=str, default=None,
        help="Process only this city (must exist in config)",
    )
    parser.add_argument(
        "--headed", action="store_true",
        help="Run browser in headed (visible) mode for debugging",
    )
    parser.add_argument(
        "--copy-to-sheets", action="store_true",
        help="Copy existing Excel data to Google Sheets and exit",
    )
    args = parser.parse_args()

    if args.copy_to_sheets:
        logger.info("Copying existing Excel data to Google Sheets...")
        gs_summary = copy_excel_to_sheets(EXCEL_FILE)
        for city, count in gs_summary.items():
            logger.info("  %s: %d row(s) copied", city, count)
        logger.info("Done copying to Google Sheets.")
        return

    if args.schedule:
        run_scheduled()
    else:
        if args.city:
            if args.city not in DEFAULT_CITIES:
                logger.error("City '%s' not found in config", args.city)
                sys.exit(1)
            cities = {args.city: DEFAULT_CITIES[args.city]}
        else:
            cities = DEFAULT_CITIES

        summary = run_pipeline(cities, headed=args.headed)
        send_email_summary(summary)

        total = sum(summary.values())
        logger.info("Done. %d new record(s) written across %d city/cities.", total, len(summary))


if __name__ == "__main__":
    main()
