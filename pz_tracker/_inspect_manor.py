"""Deeper inspection of Manor MuniCode page."""

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

        # Get all links
        all_links = await page.query_selector_all("a")
        print(f"Total links: {len(all_links)}")
        print()

        # Show ALL links (there shouldn't be too many)
        for i, a in enumerate(all_links):
            text = (await a.inner_text()).strip().replace("\n", " ")[:100]
            href = (await a.get_attribute("href")) or ""
            if text or href:
                print(f"  [{i}] text=\"{text}\"  href={href[:200]}")

        # Also check for buttons or other interactive elements
        print()
        btns = await page.query_selector_all("button, [role='button'], input[type='submit']")
        print(f"Buttons: {len(btns)}")
        for b in btns:
            text = (await b.inner_text()).strip()[:80]
            cls = (await b.get_attribute("class")) or ""
            print(f"  text=\"{text}\"  class={cls[:60]}")

        # Check for any download links or PDF references
        print()
        dl_links = await page.query_selector_all('[href*="pdf"], [href*="download"], [href*="Agenda"], [href*="Packet"]')
        print(f"Download/PDF links: {len(dl_links)}")
        for a in dl_links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip()[:80]
            print(f"  text=\"{text}\"  href={href[:200]}")

        await browser.close()

asyncio.run(main())
