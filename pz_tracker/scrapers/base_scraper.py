"""Abstract base class for all portal scrapers."""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgendaResult:
    """Represents a single agenda PDF discovered on a portal."""
    city: str
    meeting_date: str          # best-effort date string (e.g. "2026-03-02")
    pdf_url: str               # direct URL to the agenda PDF
    local_path: Path | None = None   # set after download
    secondary_pdfs: list[dict] = field(default_factory=list)
    # secondary_pdfs entries: {"url": str, "local_path": Path | None, "label": str}


class BaseScraper(abc.ABC):
    """Base interface every portal-specific scraper must implement."""

    def __init__(self, city: str, url: str) -> None:
        self.city = city
        self.url = url
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abc.abstractmethod
    async def find_latest_agenda(self, page) -> AgendaResult | None:
        """Use a Playwright *page* to locate the most recent P&Z agenda.

        Parameters
        ----------
        page : playwright.async_api.Page
            A Playwright browser page already navigated to ``self.url``.

        Returns
        -------
        AgendaResult | None
            The discovered agenda, or None if nothing was found.
        """

    async def navigate(self, page) -> None:
        """Navigate the Playwright page to the portal URL."""
        self.logger.info("Navigating to %s for %s", self.url, self.city)
        await page.goto(self.url, wait_until="domcontentloaded", timeout=30_000)
        # Give JS-rendered pages a moment to hydrate
        await page.wait_for_timeout(3000)
