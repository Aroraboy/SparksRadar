"""Scraper for MuniCode Meetings portals.

Handles two layouts:

1. **meetings.municode.com** (legacy) – URL pattern like
   ``meetings.municode.com/PublishPage/index?cid=…``.  Download links use
   the ``/d/f?u=`` wrapper.  Example: Manor.

2. **municodemeetings.com** (Drupal views table) – URL pattern like
   ``prosper-tx.municodemeetings.com``.  Each row has ``views-field-title``,
   ``views-field-field-packets``, etc.  Agenda/Packet PDFs are direct blob
   URLs on ``mccmeetings.blob.core.usgovcloudapi.net``.  Example: Prosper.
"""

from __future__ import annotations

import re
import logging
from urllib.parse import urljoin

from scrapers.base_scraper import AgendaResult, BaseScraper

logger = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(
    r"(\w+ \d{1,2},?\s*\d{4})|(\d{1,2}/\d{1,2}/\d{4})"
)

_PZ_TERMS = ["planning and zoning", "planning & zoning", "p&z", "p & z"]


class MuniCodeScraper(BaseScraper):
    """Scrape MuniCode Meetings agenda listing pages."""

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        await self.navigate(page)
        await page.wait_for_timeout(3000)

        # Detect layout variant
        if "municodemeetings.com" in self.url and "PublishPage" not in self.url:
            return await self._scrape_drupal_views(page)

        return await self._scrape_legacy(page)

    # =================================================================
    # Drupal views table (municodemeetings.com)
    # =================================================================
    async def _scrape_drupal_views(self, page) -> AgendaResult | None:
        """Handle the newer municodemeetings.com Drupal layout."""
        self.logger.info("Using Drupal views strategy for %s", self.city)

        rows = await page.query_selector_all("tr")

        for row in rows:
            title_cell = await row.query_selector(".views-field-title")
            if not title_cell:
                continue
            title_text = (await title_cell.inner_text()).strip().lower()

            # Only accept P&Z "Meeting" rows, skip "Work Session"
            if not any(t in title_text for t in _PZ_TERMS):
                continue
            if "work session" in title_text:
                continue

            # Extract date from first cell
            first_cell = await row.query_selector("td")
            cell_text = (await first_cell.inner_text()).strip() if first_cell else ""
            meeting_date = _extract_date(cell_text)

            # Gather download links from the row
            links = await row.query_selector_all("a[href]")
            packet_url = None
            agenda_url = None

            for a in links:
                href = (await a.get_attribute("href")) or ""
                href_lower = href.lower()
                if "meet-packet" in href_lower and href_lower.endswith(".pdf"):
                    packet_url = href
                elif "meet-agenda" in href_lower and href_lower.endswith(".pdf"):
                    agenda_url = href

            chosen = packet_url or agenda_url
            if chosen:
                self.logger.info(
                    "MuniCode Drupal %s: %s  date=%s  url=%s",
                    "Packet" if packet_url else "Agenda",
                    self.city, meeting_date, chosen,
                )
                return AgendaResult(
                    city=self.city,
                    meeting_date=meeting_date or "unknown",
                    pdf_url=chosen,
                )

        self.logger.warning("No P&Z agenda found on municodemeetings for %s", self.city)
        return None

    # =================================================================
    # Legacy layout (meetings.municode.com/PublishPage)
    # =================================================================
    async def _scrape_legacy(self, page) -> AgendaResult | None:
        """Handle the original meetings.municode.com /PublishPage layout."""
        # Collect all download links (href pattern: /d/f?u=...blob...)
        all_links = await page.query_selector_all('a[href*="/d/f?"]')

        packet_links: list[tuple] = []
        agenda_links: list[tuple] = []

        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            href_lower = href.lower()
            if "meet-packet" in href_lower or "agendapacket" in href_lower:
                packet_links.append((a, href))
            elif "meet-agenda" in href_lower:
                agenda_links.append((a, href))

        chosen_links = packet_links or agenda_links
        if not chosen_links:
            self.logger.warning("No agenda/packet download links found on MuniCode for %s", self.city)
            return None

        _, href = chosen_links[0]
        pdf_url = urljoin(self.url, href)

        meeting_date = _extract_date(href)
        if not meeting_date:
            parent_text = await chosen_links[0][0].evaluate(
                "el => el.closest('.meeting-item, .card, div')?.innerText || ''"
            )
            meeting_date = _extract_date(parent_text)

        link_type = "Packet" if packet_links else "Agenda"
        self.logger.info(
            "Found MuniCode %s: %s  date=%s  url=%s",
            link_type, self.city, meeting_date, pdf_url,
        )

        return AgendaResult(
            city=self.city,
            meeting_date=meeting_date or "unknown",
            pdf_url=pdf_url,
        )


def _extract_date(text: str) -> str:
    m = _DATE_PATTERN.search(text)
    return m.group(0).strip() if m else ""
