"""Scraper for standard HTML city websites.

Example city: Elgin
URL pattern: https://www.elgintexas.gov/129/Agendas-Minutes
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


class StandardHtmlScraper(BaseScraper):
    """Generic scraper for city websites that serve plain HTML agenda pages."""

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        await self.navigate(page)

        # Strategy:
        # 1. Look for direct PDF links with "agenda" in the URL or text.
        # 2. Fall back to any PDF link on the page.

        # Pass 1 – targeted search
        candidates: list[tuple] = []  # (element, href, text)
        all_links = await page.query_selector_all("a[href]")

        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            href_lower = href.lower()
            text_lower = text.lower()

            # Prioritise links that look like agendas
            is_agenda = "agenda" in text_lower or "agenda" in href_lower
            is_pdf = href_lower.endswith(".pdf") or "pdf" in href_lower

            if is_agenda and is_pdf:
                candidates.insert(0, (a, href, text))  # highest priority
            elif is_agenda:
                candidates.append((a, href, text))
            elif is_pdf and ("p&z" in text_lower or "planning" in text_lower or "zoning" in text_lower):
                candidates.append((a, href, text))

        if not candidates:
            # Pass 2 – any PDF on the page
            for a in all_links:
                href = (await a.get_attribute("href")) or ""
                if href.lower().endswith(".pdf"):
                    text = (await a.inner_text()).strip()
                    candidates.append((a, href, text))

        if not candidates:
            self.logger.warning("No agenda links found on standard HTML page for %s", self.city)
            return None

        _, href, text = candidates[0]
        pdf_url = urljoin(self.url, href)
        meeting_date = _extract_date(text)

        if not meeting_date:
            # Try the parent element for a date
            elem = candidates[0][0]
            parent = await elem.evaluate_handle("el => el.closest('li') || el.closest('tr') || el.parentElement")
            parent_text = await parent.evaluate("el => el.innerText") if parent else ""
            meeting_date = _extract_date(parent_text)

        self.logger.info(
            "Found standard-HTML agenda: %s  date=%s  url=%s",
            self.city, meeting_date, pdf_url,
        )

        return AgendaResult(
            city=self.city,
            meeting_date=meeting_date or "unknown",
            pdf_url=pdf_url,
        )


def _extract_date(text: str) -> str:
    m = _DATE_PATTERN.search(text)
    return m.group(0).strip() if m else ""
