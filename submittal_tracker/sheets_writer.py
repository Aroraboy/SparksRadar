"""Write Submittal Tracker data to Google Sheets."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from submittal_tracker.config import SHEET_COLUMNS

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Possible service-account JSON locations (checked in order)
_SA_PATHS = [
    Path(__file__).resolve().parent / "service_account.json",
    Path(__file__).resolve().parent.parent / "pz_tracker" / "service_account.json",
]


def _get_client() -> gspread.Client:
    """Authenticate with Google using service-account credentials."""
    # 1. Explicit env var path
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if creds_path:
        resolved = Path(creds_path)
        if not resolved.is_absolute():
            # relative to submittal_tracker dir
            resolved = Path(__file__).resolve().parent / creds_path
        if resolved.exists():
            creds = Credentials.from_service_account_file(str(resolved), scopes=SCOPES)
            return gspread.authorize(creds)

    # 2. Well-known paths
    for p in _SA_PATHS:
        if p.exists():
            creds = Credentials.from_service_account_file(str(p), scopes=SCOPES)
            return gspread.authorize(creds)

    # 3. Raw JSON env var
    creds_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_CREDS")
    if creds_json:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        return gspread.authorize(creds)

    raise RuntimeError(
        "Google credentials not found. Set GOOGLE_SERVICE_ACCOUNT_JSON or place "
        "service_account.json in the submittal_tracker or pz_tracker directory."
    )


def _get_or_create_sheet(
    spreadsheet: gspread.Spreadsheet,
    sheet_name: str,
) -> gspread.Worksheet:
    """Return the worksheet *sheet_name*, creating it with headers if needed."""
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=sheet_name, rows=500, cols=len(SHEET_COLUMNS)
        )
        ws.append_row(SHEET_COLUMNS, value_input_option="RAW")
        logger.info("Created new sheet tab: %s", sheet_name)
    return ws


def _existing_keys(ws: gspread.Worksheet) -> set[tuple[str, str]]:
    """Return set of (case_number, address) already in the sheet."""
    rows = ws.get_all_values()
    keys: set[tuple[str, str]] = set()
    for row in rows[1:]:
        if len(row) >= 4:
            keys.add((row[1].strip(), row[3].strip()))
    return keys


def write_rows(
    rows: list[dict],
    spreadsheet_id: str,
    sheet_name: str = "Frisco",
) -> int:
    """Append *rows* to the Google Sheet, skipping duplicates.

    Each dict must have keys matching the dataclass fields:
      case_number, project_type, address, description, status,
      submittal_date, notes, source_file, lead_priority

    Returns the number of new rows written.
    """
    client = _get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    ws = _get_or_create_sheet(spreadsheet, sheet_name)
    existing = _existing_keys(ws)

    new_rows: list[list[str]] = []
    for r in rows:
        key = (r.get("case_number", "").strip(), r.get("address", "").strip())
        if key in existing:
            continue
        existing.add(key)  # prevent intra-batch dupes
        new_rows.append([
            r.get("project_name", "Submittal Tracker"),
            r.get("case_number", ""),
            r.get("project_type", ""),
            r.get("address", ""),
            r.get("description", ""),
            r.get("status", ""),
            r.get("submittal_date", ""),
            r.get("notes", ""),
            r.get("source_file", ""),
            r.get("lead_priority", ""),
        ])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")

    logger.info(
        "Wrote %d new row(s) to sheet '%s' (%d duplicates skipped)",
        len(new_rows), sheet_name, len(rows) - len(new_rows),
    )
    return len(new_rows)
