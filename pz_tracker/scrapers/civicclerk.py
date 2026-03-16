"""Scraper for CivicClerk government portals.

Uses the public CivicClerk OData/REST API to discover the most recent P&Z
agenda PDF without needing to scrape JS-rendered React pages.

Example cities: Sherman, Elgin
API pattern:  https://{subdomain}.api.civicclerk.com/v1/
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from scrapers.base_scraper import AgendaResult, BaseScraper

logger = logging.getLogger(__name__)


class CivicClerkScraper(BaseScraper):
    """Locate the latest P&Z agenda via CivicClerk's public API."""

    def __init__(self, city: str, url: str, *, api_subdomain: str = "") -> None:
        super().__init__(city=city, url=url)
        self.api_subdomain = api_subdomain

    # ------------------------------------------------------------------

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        """*page* is accepted for interface compat but not used."""

        if not self.api_subdomain:
            # Try to derive from URL or page content
            self.api_subdomain = await self._discover_subdomain(page)

        if not self.api_subdomain:
            self.logger.warning("No CivicClerk API subdomain for %s – skipping", self.city)
            return None

        api_base = f"https://{self.api_subdomain}.api.civicclerk.com/v1"

        async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
            # 1. Find most recent *past* P&Z event with an agenda
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            resp = await client.get(
                f"{api_base}/Events",
                params={
                    "$top": "30",
                    "$orderby": "eventDate desc",
                    "$filter": f"eventDate lt {now_iso}",
                },
            )
            if resp.status_code != 200:
                self.logger.warning("CivicClerk API returned %s for %s", resp.status_code, self.city)
                return None

            events = resp.json().get("value", [])
            pz_events = [
                e for e in events
                if any(
                    kw in (e.get("eventName", "") + " " + e.get("categoryName", "")).lower()
                    for kw in ("planning", "zoning", "p&z")
                )
                and "training" not in e.get("eventName", "").lower()
                and "workshop" not in e.get("eventName", "").lower()
            ]

            if not pz_events:
                self.logger.warning("No past P&Z events found via API for %s", self.city)
                return None

            # Pick the most recent event that has a published agenda
            for event in pz_events:
                agenda_id = event.get("agendaId") or 0
                if agenda_id == 0:
                    continue

                event_date_str = event["eventDate"][:10]

                # 2. Get meeting details for published files
                mresp = await client.get(f"{api_base}/Meetings/{agenda_id}")
                if mresp.status_code != 200:
                    continue

                mdata = mresp.json()
                published_files = mdata.get("publishedFiles", [])

                # Prefer "Agenda Packet" over bare "Agenda"
                file_id = None
                for pf in published_files:
                    if pf.get("type", "").lower() == "agenda packet":
                        file_id = pf["fileId"]
                        break
                if file_id is None:
                    for pf in published_files:
                        if pf.get("type", "").lower() == "agenda":
                            file_id = pf["fileId"]
                            break

                # Fallback: use the agendaId itself as fileId
                if file_id is None:
                    file_id = agenda_id

                pdf_url = (
                    f"{api_base}/Meetings/GetMeetingFileStream"
                    f"(fileId={file_id},plainText=false)"
                )

                self.logger.info(
                    "Found CivicClerk agenda: %s  date=%s  url=%s",
                    self.city, event_date_str, pdf_url,
                )
                return AgendaResult(
                    city=self.city,
                    meeting_date=event_date_str,
                    pdf_url=pdf_url,
                )

            self.logger.warning(
                "Past P&Z events exist but none have published agendas for %s", self.city
            )
            return None

    # ------------------------------------------------------------------

    async def _discover_subdomain(self, page) -> str:
        """Navigate to the page and look for civicclerk portal links."""
        try:
            await self.navigate(page)
            links = await page.query_selector_all('a[href*="portal.civicclerk.com"]')
            for a in links:
                href = (await a.get_attribute("href")) or ""
                # href like https://SHERMANTX.portal.civicclerk.com/event/...
                if "portal.civicclerk.com" in href:
                    sub = href.split("//")[1].split(".portal.civicclerk.com")[0]
                    self.logger.info("Discovered CivicClerk subdomain: %s", sub)
                    return sub
        except Exception:
            self.logger.exception("Failed to discover CivicClerk subdomain for %s", self.city)
        return ""
