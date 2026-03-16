"""Quick test: verify updated scrapers find agendas on a few cities."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from scrapers.civicplus import CivicPlusScraper
from scrapers.municode import MuniCodeScraper

TEST_CITIES = {
    # AgendaCenter cities
    "Aubrey": {
        "url": "https://www.aubreytx.gov/AgendaCenter/Planning-Zoning-Commission-6",
        "scraper": CivicPlusScraper,
    },
    "Princeton": {
        "url": "https://princetontx.gov/AgendaCenter/Planning-Zoning-Commission-5",
        "scraper": CivicPlusScraper,
    },
    "Mesquite": {
        "url": "https://www.cityofmesquite.com/AgendaCenter/Planning-Zoning-Commission-18/",
        "scraper": CivicPlusScraper,
    },
    # municodemeetings.com city
    "Prosper": {
        "url": "https://prosper-tx.municodemeetings.com/",
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
