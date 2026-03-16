"""Debug Victoria CivicWeb page — what does the scraper actually see?"""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://victoriatx.civicweb.net/Portal/MeetingInformation.aspx?Id=491"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        title = await page.title()
        print(f"Title: {title}")

        all_links = await page.query_selector_all("a[href]")
        print(f"\nTotal links: {len(all_links)}")

        # Show all links with /document/ in href
        print("\n--- Links with /document/ ---")
        for a in all_links:
            href = (await a.get_attribute("href")) or ""
            if "/document/" in href.lower():
                text = (await a.inner_text()).strip()
                print(f"  href={href}  text='{text}'")

        # Show all links with "agenda" in text
        print("\n--- Links with 'agenda' in text ---")
        for a in all_links:
            text = (await a.inner_text()).strip()
            if "agenda" in text.lower():
                href = (await a.get_attribute("href")) or ""
                print(f"  href={href}  text='{text}'")

        # Show first 20 links for context
        print("\n--- First 20 links ---")
        for a in all_links[:20]:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip().replace("\n", " ")[:80]
            print(f"  href={href}  text='{text}'")

        await browser.close()

asyncio.run(main())
