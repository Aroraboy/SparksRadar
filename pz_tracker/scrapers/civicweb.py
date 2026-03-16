"""Scraper for CivicWeb government portals.

Example city: Victoria
URL pattern: https://victoriatx.civicweb.net/Portal/MeetingInformation.aspx?Id=491
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


class CivicWebScraper(BaseScraper):
    """Scrape CivicWeb meeting information portals."""

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        # CivicWeb can be slow — use a longer timeout
        self.logger.info("Navigating to %s for %s", self.url, self.city)
        try:
            await page.goto(self.url, wait_until="networkidle", timeout=60_000)
        except Exception:
            self.logger.info("networkidle timed out, retrying with domcontentloaded")
            await page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(3000)

        # If we're on a MeetingTypeList page, find the latest non-canceled
        # Planning Commission meeting and navigate to it.
        if "MeetingTypeList" in self.url or "MeetingInformation.aspx?type=" in self.url:
            meeting_url, meeting_date = await self._find_latest_planning_meeting(page)
            if meeting_url is None:
                self.logger.warning("No non-canceled Planning Commission meeting found for %s", self.city)
                return None
            self.logger.info("Navigating to latest meeting: %s (%s)", meeting_url, meeting_date)
            try:
                await page.goto(meeting_url, wait_until="networkidle", timeout=60_000)
            except Exception:
                await page.goto(meeting_url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_timeout(3000)
        else:
            meeting_date = ""

        # Wait for document links
        try:
            await page.wait_for_selector('a[href*="/document/"]', timeout=10_000)
        except Exception:
            self.logger.info("No /document/ links appeared within 10s for %s", self.city)

        # Victoria CivicWeb shows the current meeting info with direct links
        # like /document/NNNNN for "Agenda Packet" and "Agenda".
        # We also check the sidebar for non-canceled Planning Commission meetings.

        # Strategy 1: Direct "Agenda Packet" or "Agenda" link on current page
        all_links = await page.query_selector_all("a[href]")

        packet_link = None
        agenda_link = None

        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            text_lower = text.lower()
            href_lower = href.lower()

            if "agenda packet" in text_lower and "/document/" in href_lower:
                packet_link = href
            elif (text_lower in ("agenda", "agenda\nagenda") or text_lower.strip() == "agenda") \
                    and "/document/" in href_lower:
                agenda_link = href

        self.logger.info(
            "Victoria link search: packet=%s  agenda=%s  total_links=%d",
            packet_link, agenda_link, len(all_links),
        )

        # Prefer Agenda Packet over bare Agenda
        chosen = packet_link or agenda_link
        if chosen:
            # Ensure printPdf=true for direct PDF download
            pdf_url = urljoin(self.url, chosen)
            if "printPdf=true" not in pdf_url:
                sep = "&" if "?" in pdf_url else "?"
                pdf_url += f"{sep}printPdf=true"

            # Use meeting_date from navigation or extract from page
            if not meeting_date:
                title = await page.title()
                meeting_date = _extract_date(title)

            self.logger.info(
                "Found CivicWeb agenda: %s  date=%s  url=%s",
                self.city, meeting_date or "unknown", pdf_url,
            )
            return AgendaResult(
                city=self.city,
                meeting_date=meeting_date or "unknown",
                pdf_url=pdf_url,
            )

        self.logger.warning("No agenda links found on CivicWeb for %s", self.city)
        return None

    async def _find_latest_planning_meeting(self, page) -> tuple[str | None, str]:
        """Find the latest non-canceled Planning Commission meeting link."""
        all_links = await page.query_selector_all("a[href]")
        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            text_lower = text.lower()
            if ("planning commission" in text_lower
                    and "cancel" not in text_lower
                    and "MeetingInformation" in href
                    and "type=" not in href):
                meeting_date = _extract_date(text)
                meeting_url = urljoin(self.url, href)
                return meeting_url, meeting_date
        return None, ""


def _extract_date(text: str) -> str:
    m = _DATE_PATTERN.search(text)
    return m.group(0).strip() if m else ""
