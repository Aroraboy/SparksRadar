"""Scraper for Legistar government portals (Granicus).

Uses the public Legistar Web API to discover the most recent P&Z agenda PDF.

Example cities: McKinney, Plano, Coppell, Keller, Mansfield, Garland, etc.
API pattern:  https://webapi.legistar.com/v1/{client}/
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
import httpx
from scrapers.base_scraper import AgendaResult, BaseScraper

logger = logging.getLogger(__name__)

class LegistarScraper(BaseScraper):
    """Locate the latest P&Z agenda via Legistar's public API."""
    def __init__(self, city: str, url: str) -> None:
        super().__init__(city=city, url=url)
        # Derive client name from URL (e.g. 'mckinney' from 'https://mckinney.legistar.com/...')
        self.client = self._extract_client_name(url)

    def _extract_client_name(self, url: str) -> str:
        # e.g. https://mckinney.legistar.com/Calendar.aspx
        if '://' in url:
            host = url.split('://', 1)[1].split('/', 1)[0]
            if host.endswith('.legistar.com'):
                return host.split('.')[0]
        return ''

    async def find_latest_agenda(self, page) -> AgendaResult | None:
        if not self.client:
            self.logger.warning("No Legistar client for %s – skipping", self.city)
            return None
        api_base = f"https://webapi.legistar.com/v1/{self.client}"
        async with httpx.AsyncClient(timeout=30) as client:
            # 1. Find the P&Z body
            resp = await client.get(f"{api_base}/Bodies")
            try:
                bodies = resp.json()
            except Exception:
                self.logger.warning("Failed to parse Legistar Bodies for %s", self.city)
                return None
            if not isinstance(bodies, list):
                self.logger.warning("Legistar Bodies API error for %s: %s", self.city, bodies)
                return None
            pz_bodies = [b for b in bodies if any(kw in (b.get("BodyName", "").lower()) for kw in ["zon", "plan", "p&z", "p & z"])]
            if not pz_bodies:
                self.logger.warning("No P&Z body found for %s", self.city)
                return None
            body = pz_bodies[0]
            body_id = body["BodyId"]
            # 2. Find the latest event for this body
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            resp2 = await client.get(f"{api_base}/Events", params={
                "$filter": f"EventBodyId eq {body_id}",
                "$orderby": "EventDate desc",
                "$top": "10"
            })
            try:
                events = resp2.json()
            except Exception:
                self.logger.warning("Failed to parse Legistar Events for %s", self.city)
                return None
            if not isinstance(events, list):
                self.logger.warning("Legistar Events API error for %s: %s", self.city, events)
                return None
            for event in events:
                agenda_url = event.get("EventAgendaFile")
                meeting_date = event.get("EventDate", "")[:10]
                if not agenda_url:
                    continue
                # 3. Return the first event with an agenda PDF
                return AgendaResult(
                    city=self.city,
                    meeting_date=meeting_date,
                    pdf_url=agenda_url
                )
        return None
