"""Deduplication helpers for the Excel workbook."""

import logging

from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)


def entry_exists(ws: Worksheet, url: str | None, description: str | None) -> bool:
    """Return True if a row with the same URL **or** description already exists.

    Comparison is case-insensitive after stripping whitespace.
    Column indices (1-based) based on the standard sheet layout:
        11 = URL, 10 = Description
    """
    url_norm = (url or "").strip().lower()
    desc_norm = (description or "").strip().lower()

    for row in ws.iter_rows(min_row=2, values_only=True):
        # row index 10 → URL (col K), 9 → Description (col J)
        existing_url = str(row[10] or "").strip().lower() if len(row) > 10 else ""
        existing_desc = str(row[9] or "").strip().lower() if len(row) > 9 else ""

        if url_norm and existing_url == url_norm:
            return True
        if desc_norm and existing_desc == desc_norm:
            return True

    return False
