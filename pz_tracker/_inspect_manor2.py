"""Get the actual download links for Manor with full href and surrounding context."""

import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://meetings.municode.com/PublishPage/index?cid=MANORTX&ppid=6e8791e4-3a6b-49c1-8f3f-03e061bae9d7&p=1",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(5000)

        # Get download links that have /d/f? pattern (MuniCode download)
        dl_links = await page.query_selector_all('a[href*="/d/f"]')
        print(f"MuniCode download links: {len(dl_links)}")
        for i, a in enumerate(dl_links[:10]):
            href = (await a.get_attribute("href")) or ""
            # Get aria-label or title
            aria = (await a.get_attribute("aria-label")) or ""
            title = (await a.get_attribute("title")) or ""
            text = (await a.inner_text()).strip()[:30]
            # Get parent text for context
            parent_text = await a.evaluate("el => el.closest('.meeting-item, .card, div, tr')?.innerText?.substring(0, 120) || ''")
            print(f"\n  [{i}] href={href}")
            print(f"       aria={aria} title={title} text={text}")
            print(f"       parent: {parent_text[:100]}")

        # Also check: what is the current link the scraper grabs?
        all_links = await page.query_selector_all('a[href*=".pdf"], a[href*="Agenda"], a[href*="agenda"]')
        print(f"\nPDF/Agenda links: {len(all_links)}")
        for i, a in enumerate(all_links[:6]):
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()[:50]
            print(f"  [{i}] text=\"{text}\" href={href[:200]}")

        await browser.close()

asyncio.run(main())
