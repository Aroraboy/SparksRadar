"""Inspect Lago Vista and Manor to see Agenda vs Agenda Packet links."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # --- Lago Vista (Granicus) ---
        page = await browser.new_page()
        print("=== LAGO VISTA ===")
        await page.goto(
            "https://tx-lagovista.civicplus.com/368/Agendas-Minutes-After-April-2023",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(3000)
        iframe = await page.query_selector('iframe[src*="granicus"]')
        src = await iframe.get_attribute("src")
        await page.goto(src, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)
        rows = await page.query_selector_all("tr")
        for row in rows:
            rt = (await row.inner_text()).lower()
            if "planning" in rt and "zoning" in rt:
                print("P&Z row text:", (await row.inner_text()).strip()[:120])
                links = await row.query_selector_all("a")
                for a in links:
                    href = (await a.get_attribute("href")) or ""
                    text = (await a.inner_text()).strip()
                    print(f'  link: text="{text}"  href={href[:150]}')
                break
        await page.close()

        # --- Manor (MuniCode) ---
        page2 = await browser.new_page()
        print()
        print("=== MANOR ===")
        await page2.goto(
            "https://meetings.municode.com/PublishPage/index?cid=MANORTX&ppid=6e8791e4-3a6b-49c1-8f3f-03e061bae9d7&p=1",
            wait_until="domcontentloaded",
        )
        await page2.wait_for_timeout(5000)
        all_links = await page2.query_selector_all("a")
        print("Links with agenda/packet in text:")
        for a in all_links:
            text = (await a.inner_text()).strip()
            href = (await a.get_attribute("href")) or ""
            tl = text.lower()
            if "agenda" in tl or "packet" in tl:
                print(f'  text="{text[:80]}"  href={href[:180]}')
        await page2.close()
        await browser.close()

asyncio.run(main())
