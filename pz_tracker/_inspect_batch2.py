"""Inspect remaining unknowns more deeply."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")

CITIES = {
    "Balch Springs": "https://www.balchspringstx.gov/453/Agendas-Minutes",
    "Highland Village": "https://tx-highlandvillage2.civicplus.com/117/Agendas-Minutes",
    "Kennedale": "https://www.cityofkennedale.com/110/Agendas-Packets",
    "Flower Mound": "https://www.flowermound.gov/986/Agendas-and-Minutes",
    "Plano": "https://www.plano.gov/1251/Planning-Zoning-Commission-Agendas-Minut",
}

async def inspect_city(city, url):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

            data = await page.evaluate("""() => {
                const links = document.querySelectorAll('a[href]');
                const interesting = [];
                for (const a of links) {
                    const t = a.innerText.trim().toLowerCase();
                    const h = a.href.toLowerCase();
                    if (h.includes('agendacenter') || h.includes('archive') || 
                        h.includes('.pdf') || h.includes('granicus') || 
                        h.includes('municode') || h.includes('civicclerk') ||
                        h.includes('viewfile') || h.includes('legistar') ||
                        (t.includes('planning') && t.includes('zoning')) ||
                        (t.includes('agenda') && !t.includes('skip'))) {
                        interesting.push({text: a.innerText.trim().substring(0, 80), href: a.href.substring(0, 180)});
                    }
                }
                return interesting.slice(0, 15);
            }""")

            print(f"\n--- {city} ({url[:60]}...) ---")
            for d in data:
                print(f"  [{d['text']}] -> {d['href']}")
            if not data:
                print("  (no relevant links found)")

        except Exception as e:
            print(f"\n--- {city} ---\n  ERR: {str(e)[:100]}")
        finally:
            await browser.close()

async def main():
    for city, url in CITIES.items():
        await inspect_city(city, url)

asyncio.run(main())
