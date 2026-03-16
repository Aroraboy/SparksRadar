"""Scraper for CivicPlus government portals.

Handles two CivicPlus layouts:

1. **Granicus iframe** – The page embeds an iframe pointing at a Granicus
   meeting table.  Example: Lago Vista.

2. **AgendaCenter** – A CivicPlus‑native agenda page whose URL contains
   ``/AgendaCenter/``.  Rows use the CSS class ``catAgendaRow`` and agenda
   PDFs live at ``/AgendaCenter/ViewFile/Agenda/_MMDDYYYY‑NNN``.
   Example: Aubrey, Princeton, Mesquite.
"""

from __future__ import annotations

import re
import logging
from urllib.parse import urljoin

from scrapers.base_scraper import AgendaResult, BaseScraper

logger = logging.getLogger(__name__)

# Matches dates like "Mar 12, 2026", "March 3, 2026", or "03/03/2026"
_DATE_PATTERN = re.compile(
    r"(\w+ \d{1,2},?\s*\d{4})|(\d{1,2}/\d{1,2}/\d{4})"
)

# Terms that identify a P&Z meeting row
_PZ_TERMS = ["planning & zoning", "planning and zoning", "p&z", "p & z"]


class CivicPlusScraper(BaseScraper):
    """Scrape CivicPlus / Granicus agenda listing pages."""

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        await self.navigate(page)

        # Detect AgendaCenter layout first (URL or DOM)
        if "/AgendaCenter" in self.url or "/agendacenter" in self.url.lower():
            return await self._scrape_agenda_center(page)

        # Check DOM for AgendaCenter rows even if URL doesn't hint
        ac_rows = await page.query_selector_all("tr.catAgendaRow")
        if ac_rows:
            return await self._scrape_agenda_center(page)

        # --- Granicus iframe path ---
        return await self._scrape_granicus(page)

    # =================================================================
    # AgendaCenter layout
    # =================================================================
    async def _scrape_agenda_center(self, page) -> AgendaResult | None:
        """Handle CivicPlus AgendaCenter pages (catAgendaRow rows)."""
        self.logger.info("Using AgendaCenter strategy for %s", self.city)
        await page.wait_for_timeout(3000)

        rows = await page.query_selector_all("tr.catAgendaRow")
        if not rows:
            self.logger.warning("No catAgendaRow elements for %s", self.city)
            return await self._fallback_search(page)

        # Rows are ordered newest-first; pick the first non-cancellation row.
        for row in rows:
            row_text = (await row.inner_text()).strip()
            if "cancellation" in row_text.lower():
                continue

            meeting_date = _extract_date(row_text)

            # Prefer "Agenda Packet" link, fall back to "Agenda"
            links = await row.query_selector_all('a[href*="ViewFile"]')
            packet_link = None
            agenda_link = None
            for a in links:
                href = (await a.get_attribute("href")) or ""
                link_text = (await a.inner_text()).strip().lower()
                if "packet" in link_text or "packet" in href.lower():
                    packet_link = href
                elif not agenda_link:
                    agenda_link = href

            chosen = packet_link or agenda_link
            if chosen:
                pdf_url = urljoin(page.url, chosen)
                label = "Agenda Packet" if packet_link else "Agenda"
                self.logger.info(
                    "AgendaCenter %s: %s  date=%s  url=%s",
                    label, self.city, meeting_date, pdf_url,
                )
                return AgendaResult(
                    city=self.city,
                    meeting_date=meeting_date or "unknown",
                    pdf_url=pdf_url,
                )

        self.logger.warning("No usable agenda link in AgendaCenter for %s", self.city)
        return await self._fallback_search(page)

    # =================================================================
    # Granicus iframe layout
    # =================================================================
    async def _scrape_granicus(self, page) -> AgendaResult | None:
        """Handle the original Granicus-iframe CivicPlus layout."""
        target = page
        iframe_el = await page.query_selector(
            'iframe[src*="granicus"], iframe[src*="ViewPublisher"]'
        )
        if iframe_el:
            iframe_src = await iframe_el.get_attribute("src") or ""
            self.logger.info("Found Granicus iframe – navigating to %s", iframe_src)
            await page.goto(iframe_src, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)
            target = page

        # Find the P&Z meeting row
        rows = await target.query_selector_all("tr")
        pz_row = None
        for row in rows:
            row_text = (await row.inner_text()).strip().lower()
            if any(term in row_text for term in _PZ_TERMS):
                pz_row = row
                break

        if pz_row is None:
            self.logger.warning("No P&Z row found in Granicus table for %s", self.city)
            return await self._fallback_search(target)

        row_text = await pz_row.inner_text()
        meeting_date = _extract_date(row_text)

        # Prefer "Agenda Packet" (direct PDF) over bare "Agenda"
        pdf_links = await pz_row.query_selector_all('a[href*=".pdf"]')
        packet_link = None
        any_pdf_link = None
        for link in pdf_links:
            link_text = (await link.inner_text()).strip().lower()
            href = await link.get_attribute("href") or ""
            if not any_pdf_link:
                any_pdf_link = href
            if "packet" in link_text or "packet" in href.lower():
                packet_link = href
                break

        chosen_href = packet_link or any_pdf_link
        if chosen_href:
            pdf_url = urljoin(page.url, chosen_href)
            label = "Agenda Packet" if packet_link else "Agenda"
            self.logger.info(
                "Found %s PDF: %s  date=%s  url=%s",
                label, self.city, meeting_date, pdf_url,
            )
            return AgendaResult(
                city=self.city,
                meeting_date=meeting_date or "unknown",
                pdf_url=pdf_url,
            )

        # Archive.aspx pattern – links pointing to Archive.aspx?ADID=…
        # These directly download the PDF. Text may be like
        # "February 17, 2026 (pdf)" or "2025-10-06 Agenda PZ RM".
        archive_links = await pz_row.query_selector_all('a[href*="ADID="]')
        if not archive_links:
            archive_links = await pz_row.query_selector_all('a[href*="Archive"]')
        for a in archive_links:
            link_text = (await a.inner_text()).strip()
            # Skip cancellation entries
            if "cancellation" in link_text.lower():
                continue
            href = await a.get_attribute("href") or ""
            archive_url = urljoin(page.url, href)
            date = _extract_date(link_text)
            self.logger.info(
                "Found Archive.aspx link: %s  date=%s  url=%s",
                self.city, date, archive_url,
            )
            return AgendaResult(
                city=self.city,
                meeting_date=date or meeting_date or "unknown",
                pdf_url=archive_url,
            )

        # Fall back to AgendaViewer link
        viewer_link = await pz_row.query_selector(
            'a[href*="AgendaViewer"], a[href*="agenda"]'
        )
        if viewer_link:
            href = await viewer_link.get_attribute("href") or ""
            viewer_url = urljoin(page.url, href)
            return await self._resolve_viewer(page, viewer_url, meeting_date)

        self.logger.warning("No agenda link in P&Z row for %s", self.city)
        return await self._fallback_search(target)

    # -----------------------------------------------------------------
    async def _resolve_viewer(self, page, viewer_url: str, meeting_date: str) -> AgendaResult | None:
        """Navigate to a Granicus AgendaViewer page and find the PDF download."""
        self.logger.info("Resolving AgendaViewer page: %s", viewer_url)
        await page.goto(viewer_url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        pdf_link = await page.query_selector('a[href*=".pdf"]')
        if pdf_link:
            href = await pdf_link.get_attribute("href") or ""
            pdf_url = urljoin(page.url, href)
        else:
            pdf_url = viewer_url

        return AgendaResult(
            city=self.city,
            meeting_date=meeting_date or "unknown",
            pdf_url=pdf_url,
        )

    # -----------------------------------------------------------------
    async def _fallback_search(self, target) -> AgendaResult | None:
        """Broad link search when structured row detection fails."""
        all_links = await target.query_selector_all('a[href*=".pdf"]')
        for a in all_links:
            text = (await a.inner_text()).strip().lower()
            if "agenda" in text:
                href = await a.get_attribute("href") or ""
                pdf_url = urljoin(target.url, href)
                meeting_date = _extract_date(await a.inner_text())
                self.logger.info(
                    "Fallback found PDF: %s  date=%s  url=%s",
                    self.city, meeting_date, pdf_url,
                )
                return AgendaResult(
                    city=self.city,
                    meeting_date=meeting_date or "unknown",
                    pdf_url=pdf_url,
                )

        # Also try ViewFile links (AgendaCenter PDFs don't have .pdf in URL)
        vf_links = await target.query_selector_all('a[href*="ViewFile"]')
        for a in vf_links:
            href = await a.get_attribute("href") or ""
            pdf_url = urljoin(target.url, href)
            meeting_date = _extract_date(await a.inner_text())
            self.logger.info(
                "Fallback found ViewFile link: %s  date=%s  url=%s",
                self.city, meeting_date, pdf_url,
            )
            return AgendaResult(
                city=self.city,
                meeting_date=meeting_date or "unknown",
                pdf_url=pdf_url,
            )

        self.logger.warning("No agenda PDF found at all for %s", self.city)
        return None


def _extract_date(text: str) -> str:
    """Return the first date-like substring found in *text*, or ''."""
    m = _DATE_PATTERN.search(text)
    return m.group(0).strip() if m else ""
