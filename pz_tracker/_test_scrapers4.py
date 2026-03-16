"""Test Archive.aspx fix + inspect Cedar Park/Leander/Quinlan."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from scrapers.civicplus import CivicPlusScraper

async def test_midlothian():
    from playwright.async_api import async_playwright
    scraper = CivicPlusScraper(city="Midlothian", url="https://www.midlothian.tx.us/Archive.aspx?AMID=32")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            result = await scraper.find_latest_agenda(page)
            if result:
                print(f"  OK  Midlothian: date={result.meeting_date}  url={result.pdf_url[:120]}")
            else:
                print(f"  FAIL  Midlothian: no result")
        except Exception as e:
            print(f"  ERR  Midlothian: {e}")
        finally:
            await browser.close()

async def inspect_page(city, url):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        # Check for iframes
        iframes = await page.query_selector_all("iframe")
        iframe_srcs = []
        for f in iframes:
            src = await f.get_attribute("src") or ""
            if src and src != "about:blank":
                iframe_srcs.append(src[:150])

        # Check for catAgendaRow
        ac_rows = await page.query_selector_all("tr.catAgendaRow")

        # Check for P&Z in any rows
        pz_found = False
        rows = await page.query_selector_all("tr")
        for r in rows:
            rt = (await r.inner_text()).strip().lower()
            if any(t in rt for t in ["planning & zoning", "p&z", "planning and zoning"]):
                pz_found = True
                break

        # Check all links mentioning PDF or agenda
        pdf_links = await page.evaluate("""() => {
            const links = document.querySelectorAll('a[href]');
            return Array.from(links).filter(a => {
                const h = a.href.toLowerCase();
                const t = a.innerText.toLowerCase();
                return h.includes('.pdf') || h.includes('agenda') || h.includes('viewfile') || t.includes('agenda');
            }).slice(0, 10).map(a => ({text: a.innerText.trim().substring(0, 60), href: a.href.substring(0, 150)}));
        }""")

        print(f"\n--- {city} ---")
        print(f"  Iframes: {iframe_srcs}")
        print(f"  catAgendaRow: {len(ac_rows)}")
        print(f"  P&Z row found: {pz_found}")
        print(f"  Relevant links ({len(pdf_links)}):")
        for l in pdf_links[:8]:
            print(f"    [{l['text']}] -> {l['href']}")

        await browser.close()

async def main():
    await test_midlothian()
    await inspect_page("Cedar Park", "https://www.cedarparktexas.gov/591/Planning-Zoning-Agendas")
    await inspect_page("Leander", "https://www.leandertx.gov/129/Agendas-Minutes")
    await inspect_page("Quinlan", "https://tx-quinlan.civicplus.com/Archive.aspx?AMID=53")

asyncio.run(main())
