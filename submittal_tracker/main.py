"""Submittal Tracker – main entry point.

Usage:
    python -m submittal_tracker.main --city Frisco --sheet-id <GOOGLE_SHEET_ID> [--year 2026]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Load .env from pz_tracker (shared credentials)
_pz_env = Path(__file__).resolve().parent.parent / "pz_tracker" / ".env"
if _pz_env.exists():
    load_dotenv(_pz_env)
# Also try local .env
load_dotenv()

from submittal_tracker.config import CITIES
from submittal_tracker.scraper import discover_documents
from submittal_tracker.extractor import download_pdf, extract_from_pdf
from submittal_tracker.sheets_writer import write_rows
from submittal_tracker.webhook_writer import send_submittal_records

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("submittal_tracker")


async def run(city: str, spreadsheet_id: str, year_filter: int | None = None) -> None:
    """Discover, extract, and write submittal data for *city*."""
    city_cfg = CITIES.get(city)
    if not city_cfg:
        logger.error("Unknown city: %s.  Available: %s", city, list(CITIES.keys()))
        return

    archive_url = city_cfg["archive_url"]
    base_url = city_cfg["base_url"]
    pdf_url_template = city_cfg["pdf_url_template"]

    # 1. Discover all documents
    logger.info("Discovering documents for %s …", city)
    docs = await discover_documents(
        archive_url, base_url, pdf_url_template, year_filter=year_filter,
    )
    if not docs:
        logger.warning("No documents found for %s", city)
        return

    logger.info("Found %d documents for %s", len(docs), city)

    total_written = 0

    # 2. Process each document
    for doc in docs:
        submittal_date = doc.parsed_date.strftime("%Y-%m-%d")
        logger.info(
            "Processing %s (ADID=%d, date=%s) …", doc.date_label, doc.adid, submittal_date
        )

        pdf_bytes = download_pdf(doc.pdf_url)
        if not pdf_bytes:
            logger.warning("Skipping %s – download failed", doc.date_label)
            continue

        rows = extract_from_pdf(pdf_bytes, doc.pdf_url, submittal_date)
        if not rows:
            logger.info("No data rows found in %s", doc.date_label)
            continue

        # Convert dataclass rows to dicts
        row_dicts = [asdict(r) for r in rows]

        written = write_rows(row_dicts, spreadsheet_id, sheet_name=city)
        total_written += written
        logger.info(
            "  → %d new rows from %s (%d total so far)", written, doc.date_label, total_written
        )

        # Send to Replit webhook
        webhook_sent = send_submittal_records(row_dicts, city=city)
        if webhook_sent:
            logger.info("  → Webhook: %d record(s) sent", webhook_sent)

        # Polite delay between documents
        time.sleep(1.5)

    logger.info("Done!  %d total new rows written for %s.", total_written, city)


def main() -> None:
    parser = argparse.ArgumentParser(description="Submittal Tracker – extract & populate Google Sheets")
    parser.add_argument("--city", default="Frisco", help="City name (default: Frisco)")
    parser.add_argument("--sheet-id", required=True, help="Google Spreadsheet ID")
    parser.add_argument("--year", type=int, default=None, help="Only process documents from this year onward (e.g. 2025)")
    args = parser.parse_args()

    asyncio.run(run(args.city, args.sheet_id, args.year))


if __name__ == "__main__":
    main()
