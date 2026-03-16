"""Inspect CivicClerk event detail page for Sherman."""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Navigate to a recent Sherman P&Z event
        url = "https://SHERMANTX.portal.civicclerk.com/event/1354/files"
        print(f"Navigating to {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Dump all links
        links = await page.query_selector_all("a[href]")
        print(f"\nLinks ({len(links)}):")
        for a in links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip().replace("\n", " ")[:120]
            if href and text:
                print(f"  href={href}")
                print(f"    text={text}")

        # Also check for buttons or downloadable items
        buttons = await page.query_selector_all("button, [role='button']")
        print(f"\nButtons ({len(buttons)}):")
        for btn in buttons:
            text = (await btn.inner_text()).strip().replace("\n", " ")[:100]
            cls = (await btn.get_attribute("class")) or ""
            if text:
                print(f"  class={cls[:60]}  text={text}")

        # Check for any download-related elements
        download_els = await page.query_selector_all('[href*="download"], [href*="FileStream"], [href*=".pdf"], [data-url]')
        print(f"\nDownload elements ({len(download_els)}):")
        for el in download_els:
            tag = await el.evaluate("el => el.tagName")
            href = (await el.get_attribute("href")) or (await el.get_attribute("data-url")) or ""
            text = (await el.inner_text()).strip()[:80]
            print(f"  tag={tag} href={href} text={text}")

        await browser.close()

asyncio.run(main())
