"""Inspect AgendaCenter page structure."""
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        
        await page.goto(
            "https://www.aubreytx.gov/AgendaCenter/Planning-Zoning-Commission-6",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(5000)
        
        print("=== URL:", page.url)

        # Look for ViewFile links (CivicPlus AgendaCenter pattern)
        view_links = await page.query_selector_all('a[href*="ViewFile"]')
        print(f"\nViewFile links: {len(view_links)}")
        for link in view_links[:10]:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()
            print(f"  [{text[:60]}] -> {href[:120]}")

        # Look for PDF links
        pdf_links = await page.query_selector_all('a[href*=".pdf"]')
        print(f"\nPDF links: {len(pdf_links)}")
        for link in pdf_links[:10]:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()
            print(f"  [{text[:60]}] -> {href[:120]}")

        # Look for Agenda-related divs/sections
        agenda_els = await page.query_selector_all('[class*="agenda" i], [class*="Agenda"]')
        print(f"\nAgenda elements: {len(agenda_els)}")
        for el in agenda_els[:10]:
            cls = await el.get_attribute("class") or ""
            tag = await el.evaluate("el => el.tagName")
            text = (await el.inner_text()).strip()[:80]
            print(f"  {tag}.{cls}: {text}")

        # Get table rows with substance
        trs = await page.query_selector_all("tr")
        print(f"\nTable rows with content: (of {len(trs)} total)")
        for tr in trs[:20]:
            text = (await tr.inner_text()).strip()
            if text and len(text) > 5:
                cls = await tr.get_attribute("class") or ""
                print(f"  [{cls}] {text[:100]}")

        # Check for any links at all
        all_links = await page.query_selector_all("a[href]")
        agenda_links = []
        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()
            if "agenda" in href.lower() or "agenda" in text.lower():
                agenda_links.append((text[:60], href[:120]))
        print(f"\nAll 'agenda'-related links: {len(agenda_links)}")
        for text, href in agenda_links[:15]:
            print(f"  [{text}] -> {href}")

        await browser.close()

asyncio.run(inspect())
