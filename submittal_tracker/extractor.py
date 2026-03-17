"""Extract structured rows from Submittal Tracker PDFs."""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field

import httpx
import pdfplumber

from submittal_tracker.config import (
    HIGH_PRIORITY_KEYWORDS,
    MEDIUM_PRIORITY_KEYWORDS,
    PROJECT_TYPE_MAP,
)

logger = logging.getLogger(__name__)


@dataclass
class SubmittalRow:
    """One project row extracted from a Submittal Tracker PDF."""
    project_name: str        # always "Submittal Tracker"
    case_number: str
    project_type: str
    address: str
    description: str
    status: str
    submittal_date: str      # YYYY-MM-DD
    notes: str               # planner name
    source_file: str         # PDF URL
    lead_priority: str       # High / Medium / Low


def extract_from_pdf(
    pdf_bytes: bytes,
    pdf_url: str,
    submittal_date: str,
) -> list[SubmittalRow]:
    """Parse all project rows from a single Submittal Tracker PDF.

    Parameters
    ----------
    pdf_bytes : raw PDF content
    pdf_url : URL of the source file (for Source File column)
    submittal_date : formatted date string YYYY-MM-DD
    """
    rows: list[SubmittalRow] = []

    try:
        pdf = pdfplumber.open(io.BytesIO(pdf_bytes))
    except Exception:
        logger.exception("Failed to open PDF: %s", pdf_url)
        return rows

    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if not table or len(table[0]) < 4:
                continue

            # Check if header row matches expected columns
            header = [_clean(c) for c in table[0]]
            if "PROJECT #" not in header[0].upper():
                continue

            for data_row in table[1:]:
                if len(data_row) < 4:
                    continue

                case_number = _clean(data_row[0])
                if not case_number:
                    continue

                name = _clean(data_row[1])
                description = _clean(data_row[2])
                planner = _clean(data_row[4]) if len(data_row) > 4 else ""

                project_type = _derive_type(case_number)
                priority = _derive_priority(description)

                rows.append(SubmittalRow(
                    project_name="Submittal Tracker",
                    case_number=case_number,
                    project_type=project_type,
                    address=name,
                    description=description,
                    status="Submitted",
                    submittal_date=submittal_date,
                    notes=planner,
                    source_file=pdf_url,
                    lead_priority=priority,
                ))

    pdf.close()
    logger.info("Extracted %d rows from %s", len(rows), pdf_url)
    return rows


def download_pdf(url: str, *, timeout: int = 60) -> bytes | None:
    """Download a PDF and return raw bytes, or None on failure."""
    try:
        r = httpx.get(url, follow_redirects=True, timeout=timeout)
        if r.status_code == 200 and len(r.content) > 100:
            return r.content
        logger.warning("Bad response %s for %s", r.status_code, url)
    except Exception:
        logger.exception("Download failed: %s", url)
    return None


# ── helpers ────────────────────────────────────────────────────────


def _clean(value: str | None) -> str:
    """Normalise whitespace and strip a cell value."""
    if not value:
        return ""
    return " ".join(value.split())


def _derive_type(case_number: str) -> str:
    """Derive a human-readable project type from the case-number prefix."""
    # Case numbers look like CP26-0007, FP26-0006, PSP26-0002, etc.
    m = re.match(r"^([A-Z]+)", case_number)
    if m:
        prefix = m.group(1)
        return PROJECT_TYPE_MAP.get(prefix, prefix)
    return ""


def _derive_priority(description: str) -> str:
    """Assign lead priority based on description keywords."""
    desc_lower = description.lower()
    for kw in HIGH_PRIORITY_KEYWORDS:
        if kw in desc_lower:
            return "High"
    for kw in MEDIUM_PRIORITY_KEYWORDS:
        if kw in desc_lower:
            return "Medium"
    return "Low"
