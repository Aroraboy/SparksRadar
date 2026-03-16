"""Inspect remaining non-AgendaCenter CivicPlus cities to determine layout."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")

CITIES = {
    "Leander": "https://www.leandertx.gov/129/Agendas-Minutes",
    "Little Elm": "https://www.littleelm.org/1258/Agendas-Minutes-Videos",
    "Highland Village": "https://tx-highlandvillage2.civicplus.com/117/Agendas-Minutes",
    "Sanger": "https://sangertexas.org/129/Agendas-Minutes",
    "Roanoke": "https://roanoketexas.com/121/Agendas-Minutes",
    "Grapevine": "https://www.grapevinetexas.gov/89/Agendas-Minutes",
    "Trophy Club": "https://www.trophyclub.org/809/Agendas-and-Minutes",
    "Kennedale": "https://www.cityofkennedale.com/110/Agendas-Packets",
    "Alvarado": "https://www.cityofalvarado.org/129/Agendas-Minutes",
    "Balch Springs": "https://www.balchspringstx.gov/453/Agendas-Minutes",
    "Wilmer": "https://www.cityofwilmer.net/244/Agendas-Minutes",
    "Kaufman": "https://www.kaufmantx.org/2160/Agendas-Minutes",
    "Flower Mound": "https://www.flowermound.gov/986/Agendas-and-Minutes",
    "Plano": "https://www.plano.gov/1251/Planning-Zoning-Commission-Agendas-Minut",
    "Seagoville": "https://seagoville.us/Archive.aspx?AMID=36",
}

async def inspect_city(city, url):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            info = await page.evaluate("""() => {
                // iframes
                const iframes = Array.from(document.querySelectorAll('iframe'))
                    .map(f => f.src).filter(s => s && s !== 'about:blank');
                // catAgendaRow
                const acRows = document.querySelectorAll('tr.catAgendaRow').length;
                // ADID links
                const adidLinks = document.querySelectorAll('a[href*="ADID="]').length;
                // Granicus
                const granicusIframes = document.querySelectorAll('iframe[src*="granicus"], iframe[src*="ViewPublisher"]').length;
                // MuniCode iframe
                const municodeIframes = document.querySelectorAll('iframe[src*="municode"]').length;
                // P&Z in any text
                const body = document.body.innerText.toLowerCase();
                const hasPZ = body.includes('planning & zoning') || body.includes('planning and zoning') || body.includes('p&z');
                // AgendaCenter links
                const agendaCenterLinks = document.querySelectorAll('a[href*="AgendaCenter"]').length;
                
                return {iframes: iframes.slice(0, 3), acRows, adidLinks, granicusIframes, municodeIframes, hasPZ, agendaCenterLinks};
            }""")

            layout = "UNKNOWN"
            if info["acRows"] > 0: layout = "AgendaCenter"
            elif info["granicusIframes"] > 0: layout = "Granicus iframe"
            elif info["municodeIframes"] > 0: layout = "MuniCode iframe"
            elif info["adidLinks"] > 0: layout = "Archive.aspx"
            elif info["agendaCenterLinks"] > 0: layout = "Links to AgendaCenter"

            print(f"  {city:20s}  {layout:25s}  PZ={info['hasPZ']}  iframes={info['iframes'][:2]}")

        except Exception as e:
            print(f"  {city:20s}  ERR: {str(e)[:80]}")
        finally:
            await browser.close()

async def main():
    for city, url in CITIES.items():
        await inspect_city(city, url)

asyncio.run(main())
