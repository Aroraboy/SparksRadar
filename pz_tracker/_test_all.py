"""Test all newly reconfigured cities (scraping only, no downloads)."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")

from config import DEFAULT_CITIES
from scrapers.civicplus import CivicPlusScraper
from scrapers.municode import MuniCodeScraper
from scrapers.civicclerk import CivicClerkScraper
from scrapers.civicweb import CivicWebScraper
from scrapers.standard_html import StandardHtmlScraper

SCRAPER_MAP = {
    "civicplus": CivicPlusScraper,
    "municode": MuniCodeScraper,
    "civicclerk": CivicClerkScraper,
    "civicweb": CivicWebScraper,
    "standard_html": StandardHtmlScraper,
}

# Skip the original 5 already-working cities
SKIP = {"Lago Vista", "Manor", "Sherman", "Victoria", "Elgin", "Glenn Heights", "Taylor", "Terrell"}

async def test_city(city, info):
    from playwright.async_api import async_playwright
    portal_type = info.get("portal_type", "standard_html")
    scraper_cls = SCRAPER_MAP.get(portal_type)
    if not scraper_cls:
        return city, "SKIP", f"unknown portal: {portal_type}"
    
    kwargs = {"city": city, "url": info["url"]}
    if portal_type == "civicclerk" and info.get("api_subdomain"):
        kwargs["api_subdomain"] = info["api_subdomain"]
    
    scraper = scraper_cls(**kwargs)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            result = await scraper.find_latest_agenda(page)
            if result:
                return city, "OK", f"date={result.meeting_date}  url={result.pdf_url[:90]}"
            else:
                return city, "FAIL", "no result"
        except Exception as e:
            return city, "ERR", str(e)[:80]
        finally:
            await browser.close()

async def main():
    ok = fail = err = 0
    for city, info in DEFAULT_CITIES.items():
        if city in SKIP:
            continue
        c, status, msg = await test_city(city, info)
        portal = info.get("portal_type", "?")
        icon = {"OK": "✓", "FAIL": "✗", "ERR": "!"}[status]
        print(f"  {icon} {c:20s} [{portal:12s}] {msg}")
        if status == "OK": ok += 1
        elif status == "FAIL": fail += 1
        else: err += 1

    print(f"\n  Summary: {ok} OK, {fail} FAIL, {err} ERR (of {ok+fail+err} tested)")

asyncio.run(main())
