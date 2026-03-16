"""Download helper with retry logic for fetching PDFs."""

import logging
import time
from pathlib import Path

import httpx

from config import DOWNLOAD_DIR, MAX_RETRIES, PDF_DOWNLOAD_TIMEOUT, REQUEST_DELAY_SECONDS

logger = logging.getLogger(__name__)


def _sanitise_filename(name: str) -> str:
    """Remove characters that are unsafe in file-system paths."""
    keep = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
    return "".join(c if c in keep else "_" for c in name).strip("_")


def download_pdf(url: str, dest_dir: Path | None = None, filename: str | None = None) -> Path | None:
    """Download a PDF from *url* into *dest_dir* and return the local path.

    Retries up to ``MAX_RETRIES`` times on transient failures.
    Returns ``None`` when all attempts are exhausted.
    """
    dest_dir = dest_dir or DOWNLOAD_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        # Derive filename from the URL path component
        url_path = httpx.URL(url).path
        filename = _sanitise_filename(Path(url_path).name) or "agenda.pdf"
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

    dest_path = dest_dir / filename

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info("Downloading (attempt %d/%d): %s", attempt, MAX_RETRIES, url)
            with httpx.Client(timeout=PDF_DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()

            # Validate the response is actually a PDF
            content_type = resp.headers.get("content-type", "").lower()
            if "pdf" not in content_type and not resp.content[:5].startswith(b"%PDF"):
                logger.warning(
                    "Response is not a PDF (content-type=%s, first bytes=%r) – skipping",
                    content_type, resp.content[:20],
                )
                return None

            dest_path.write_bytes(resp.content)
            logger.info("Saved PDF → %s (%d bytes)", dest_path, len(resp.content))
            return dest_path

        except (httpx.HTTPStatusError, httpx.RequestError) as exc:
            logger.warning("Download attempt %d failed: %s", attempt, exc)
            if attempt < MAX_RETRIES:
                time.sleep(REQUEST_DELAY_SECONDS)

    logger.error("All %d download attempts failed for %s", MAX_RETRIES, url)
    return None
