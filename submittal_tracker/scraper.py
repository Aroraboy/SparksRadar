"""Scrape the Frisco archive page to discover all Submittal Tracker PDF links."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime

import httpx
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


@dataclass
class ArchiveDocument:
    """One submittal-tracker PDF discovered on the archive page."""
    adid: int
    date_label: str          # e.g. "February 23, 2026"
    parsed_date: datetime
    pdf_url: str


async def discover_documents(
    archive_url: str,
    base_url: str,
    pdf_url_template: str,
    *,
    year_filter: int | None = None,
) -> list[ArchiveDocument]:
    """Return all Submittal Tracker documents from *archive_url*.

    If *year_filter* is given, only documents from January of that year
    onward are returned.
    """
    docs: list[ArchiveDocument] = []
    seen_adids: set[int] = set()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(archive_url, timeout=20_000, wait_until="networkidle")

        links = await page.query_selector_all("a")
        for link in links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()

            # Match links like Archive.aspx?ADID=3626
            m = re.search(r"ADID=(\d+)", href)
            if not m:
                continue
            adid = int(m.group(1))
            if adid in seen_adids:
                continue

            # Parse the date from the link text
            parsed = _parse_date_label(text)
            if parsed is None:
                continue

            if year_filter and parsed.year < year_filter:
                continue

            seen_adids.add(adid)
            pdf_url = pdf_url_template.format(adid=adid)
            docs.append(ArchiveDocument(
                adid=adid,
                date_label=text,
                parsed_date=parsed,
                pdf_url=pdf_url,
            ))

        await browser.close()

    # Sort chronologically (oldest first)
    docs.sort(key=lambda d: d.parsed_date)
    logger.info("Discovered %d submittal documents from %s", len(docs), archive_url)
    return docs


_DATE_PATTERNS = [
    r"(\w+ \d{1,2},?\s*\d{4})",   # "February 23, 2026"
    r"(\w+ \d{1,2}(?:st|nd|rd|th),?\s*\d{4})",  # "April 29th, 2024"
]

_DATE_FORMATS = [
    "%B %d, %Y",
    "%B %d %Y",
    "%B %d,%Y",
    "%B %dst, %Y",
    "%B %dnd, %Y",
    "%B %drd, %Y",
    "%B %dth, %Y",
    "%B %dst %Y",
    "%B %dnd %Y",
    "%B %drd %Y",
    "%B %dth %Y",
]


def _parse_date_label(text: str) -> datetime | None:
    """Try to parse a date from an archive link label."""
    # Normalise whitespace
    text = " ".join(text.split())
    for pattern in _DATE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            date_str = m.group(1)
            # Strip ordinal suffixes
            date_str = re.sub(r"(\d)(st|nd|rd|th)", r"\1", date_str)
            for fmt in _DATE_FORMATS:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
    return None
