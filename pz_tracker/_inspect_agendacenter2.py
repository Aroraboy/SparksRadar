"""Inspect AgendaCenter and MuniCodeMeetings pages."""
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        # --- Check Princeton AgendaCenter ---
        page = await browser.new_page()
        await page.goto(
            "https://princetontx.gov/AgendaCenter/Planning-Zoning-Commission-5",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(5000)
        print("=== PRINCETON ===")
        rows = await page.query_selector_all("tr.catAgendaRow")
        print(f"catAgendaRow count: {len(rows)}")
        for row in rows[:3]:
            text = (await row.inner_text()).strip()[:120]
            print(f"  {text}")
            links = await row.query_selector_all('a[href*="ViewFile"]')
            for link in links:
                href = await link.get_attribute("href") or ""
                lt = (await link.inner_text()).strip()
                print(f"    [{lt[:40]}] -> {href}")
        await page.close()

        # --- Check Prosper MuniCodeMeetings ---
        page = await browser.new_page()
        await page.goto(
            "https://prosper-tx.municodemeetings.com/",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(5000)
        print("\n=== PROSPER (municodemeetings.com) ===")
        print("URL:", page.url)
        
        # Check for meeting links
        all_links = await page.query_selector_all("a[href]")
        pz_links = []
        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            tl = text.lower()
            if "planning" in tl or "zoning" in tl or "p&z" in tl or "p & z" in tl:
                pz_links.append((text[:80], href[:120]))
        print(f"P&Z links: {len(pz_links)}")
        for text, href in pz_links[:10]:
            print(f"  [{text}] -> {href}")

        # Check for download links
        dl_links = await page.query_selector_all('a[href*="/d/f?"], a[href*=".pdf"], a[href*="Packet"], a[href*="packet"]')
        print(f"Download links: {len(dl_links)}")
        for a in dl_links[:10]:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            print(f"  [{text[:60]}] -> {href[:120]}")
        
        # Check page structure
        cards = await page.query_selector_all('[class*="meeting"], [class*="Meeting"], .card, .list-group-item')
        print(f"Meeting cards/items: {len(cards)}")
        for c in cards[:5]:
            text = (await c.inner_text()).strip()[:100]
            cls = await c.get_attribute("class") or ""
            print(f"  [{cls[:40]}] {text}")

        await browser.close()

asyncio.run(inspect())
