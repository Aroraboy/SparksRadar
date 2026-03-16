"""Test non-AgendaCenter CivicPlus cities and other variants."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from scrapers.civicplus import CivicPlusScraper
from scrapers.municode import MuniCodeScraper

TEST_CITIES = {
    # Original Granicus iframe city (should still work)
    "Lago Vista": {
        "url": "https://tx-lagovista.civicplus.com/368/Agendas-Minutes-After-April-2023",
        "scraper": CivicPlusScraper,
    },
    # Archive.aspx variants
    "Midlothian": {
        "url": "https://www.midlothian.tx.us/Archive.aspx?AMID=32",
        "scraper": CivicPlusScraper,
    },
    # More AgendaCenter cities
    "Forney": {
        "url": "https://www.forneytx.gov/AgendaCenter/Planning-Zoning-Commission-5",
        "scraper": CivicPlusScraper,
    },
    "Cleburne": {
        "url": "https://www.cleburne.net/AgendaCenter/Planning-Zoning-Commission-15",
        "scraper": CivicPlusScraper,
    },
    # Another municodemeetings city
    "Burleson": {
        "url": "https://burleson-tx.municodemeetings.com/",
        "scraper": MuniCodeScraper,
    },
}

async def test_city(city, info):
    from playwright.async_api import async_playwright
    scraper = info["scraper"](city=city, url=info["url"])
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            result = await scraper.find_latest_agenda(page)
            if result:
                print(f"  OK  {city}: date={result.meeting_date}  url={result.pdf_url[:100]}")
            else:
                print(f"  FAIL  {city}: no result")
        except Exception as e:
            print(f"  ERR  {city}: {e}")
        finally:
            await browser.close()

async def main():
    for city, info in TEST_CITIES.items():
        await test_city(city, info)

asyncio.run(main())
