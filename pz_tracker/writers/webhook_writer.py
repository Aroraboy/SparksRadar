"""Webhook writer – POST scraped P&Z records to the Replit app."""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)


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
    payload = {
        "source": "pz_tracker",
        "city": city,
        "records": records,
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
