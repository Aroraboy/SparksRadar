"""Check Victoria meeting list and schedule pages."""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Check meeting type list
        url = "https://victoriatx.civicweb.net/Portal/MeetingTypeList.aspx"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(3000)

        links = await page.query_selector_all("a[href]")
        print(f"Links: {len(links)}")
        for a in links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip().replace("\n", " ")[:80]
            if "planning" in text.lower() or "commission" in text.lower():
                print(f"  href={href}  text={text}")

        await browser.close()

asyncio.run(main())
