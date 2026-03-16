"""Test Midlothian and other Archive.aspx cities."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from scrapers.civicplus import CivicPlusScraper

TEST_CITIES = {
    "Midlothian": {
        "url": "https://www.midlothian.tx.us/Archive.aspx?AMID=32",
    },
    "Rowlett": {
        "url": "https://www.rowletttx.gov/Archive.aspx?AMID=53",
    },
    "Quinlan": {
        "url": "https://tx-quinlan.civicplus.com/Archive.aspx?AMID=53",
    },
    # Non-AgendaCenter, non-Archive: check what strategy they use
    "Cedar Park": {
        "url": "https://www.cedarparktexas.gov/591/Planning-Zoning-Agendas",
    },
    "Leander": {
        "url": "https://www.leandertx.gov/129/Agendas-Minutes",
    },
}

async def test_city(city, info):
    from playwright.async_api import async_playwright
    scraper = CivicPlusScraper(city=city, url=info["url"])
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            result = await scraper.find_latest_agenda(page)
            if result:
                print(f"  OK  {city}: date={result.meeting_date}  url={result.pdf_url[:120]}")
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
