"""Webhook writer – POST scraped P&Z records to the Replit app."""

from __future__ import annotations

import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)


def _transform_record(rec: dict, city: str, idx: int) -> dict:
    """Map P&Z extractor fields to the Replit common schema.

    The Replit webhook expects: address (required), project_type,
    description, submittal_date, case_number, status, source_file,
    notes, and land_acres as a *numeric* value.  Null-valued fields
    must be omitted entirely (JSON null causes the record to be
    skipped server-side).
    """
    safe_city = city.upper().replace(" ", "")
    out: dict = {"case_number": f"PZ-{safe_city}-{idx:03d}", "status": "Pending"}

    # Map P&Z → common schema names
    mapping = {
        "location": "address",
        "construction_type": "project_type",
        "pz_meeting_date": "submittal_date",
        "url": "source_file",
        "description": "description",
    }
    for src, dst in mapping.items():
        val = rec.get(src)
        if val:
            out[dst] = str(val)

    # Also add pz_meeting_date as itself for Replit to store
    if rec.get("pz_meeting_date"):
        out["pz_meeting_date"] = str(rec["pz_meeting_date"])

    # land_acres: must be numeric, not a string like "12.5 acres"
    raw_acres = rec.get("land_acres")
    if raw_acres:
        m = re.search(r"[\d.]+", str(raw_acres))
        if m:
            try:
                out["land_acres"] = float(m.group())
            except ValueError:
                pass

    # Pass through simple string fields, omitting None values
    for field in ("owner_name", "general_contractor", "architect",
                  "applicant_name", "applicant_email", "applicant_phone"):
        val = rec.get(field)
        if val:
            out[field] = str(val)

    # Build notes with P&Z extras for context
    extras = []
    if rec.get("owner_name"):
        extras.append(f"Owner: {rec['owner_name']}")
    if rec.get("general_contractor"):
        extras.append(f"GC: {rec['general_contractor']}")
    if rec.get("architect"):
        extras.append(f"Architect: {rec['architect']}")
    if raw_acres:
        extras.append(f"Land: {raw_acres}")
    if extras:
        out["notes"] = " | ".join(extras)

    out["city"] = city
    return out


def send_pz_records(records: list[dict], city: str) -> int:
    """Send P&Z records to the Replit webhook endpoint.

    Returns the number of records sent, or 0 if the webhook is not
    configured or the request fails.  Failures are logged but never
    raise – the rest of the pipeline continues regardless.
    """
    webhook_url = os.environ.get("REPLIT_WEBHOOK_URL", "").rstrip("/")
    pipeline_secret = os.environ.get("PIPELINE_SECRET", "")

    if not webhook_url or not pipeline_secret:
        logger.debug("Webhook not configured – skipping")
        return 0

    url = f"{webhook_url}/api/webhooks/permits"
    transformed = [_transform_record(r, city, i + 1) for i, r in enumerate(records)]
    payload = {
        "source": "pz_tracker",
        "city": city,
        "records": transformed,
    }
    headers = {
        "Content-Type": "application/json",
        "X-Pipeline-Key": pipeline_secret,
    }

    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info("Webhook: sent %d record(s) for %s → %s", len(records), city, resp.status_code)
        return len(records)
    except httpx.HTTPStatusError as exc:
        logger.warning("Webhook returned %s for %s: %s", exc.response.status_code, city, exc.response.text[:200])
    except Exception:
        logger.exception("Webhook request failed for %s", city)

    return 0
