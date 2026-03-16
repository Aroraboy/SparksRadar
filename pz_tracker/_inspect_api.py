"""Inspect CivicClerk API for Sherman and Elgin."""

import asyncio
from playwright.async_api import async_playwright
import json


async def try_api(page, label, url):
    print(f"\n--- {label} ---")
    print(f"  URL: {url}")
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        content = await page.content()
        # Try to extract body text
        body = await page.query_selector("body")
        text = (await body.inner_text())[:3000] if body else content[:3000]
        # Try to parse as JSON
        try:
            data = json.loads(text)
            print(f"  JSON response:")
            print(json.dumps(data, indent=2)[:2000])
        except:
            print(f"  Text response ({len(text)} chars):")
            print(text[:1500])
    except Exception as e:
        print(f"  ERROR: {e}")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Try CivicClerk API for Sherman event 1354
        await try_api(page, "Sherman Event 1354",
                      "https://SHERMANTX.api.civicclerk.com/v1/Events/1354")

        await try_api(page, "Sherman Event 1354 Files (OData)",
                      "https://SHERMANTX.api.civicclerk.com/v1/Events(1354)/EventFiles")

        await try_api(page, "Sherman Event 1354 Meeting files",
                      "https://SHERMANTX.api.civicclerk.com/v1/Events(1354)?$expand=EventFiles")

        # Try file stream directly (from previous inspection)
        await try_api(page, "Sherman FileStream 2384 (plainText=false)",
                      "https://SHERMANTX.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=2384,plainText=false)")

        # Also try Elgin event 2365 (recent P&Z)
        await try_api(page, "Elgin Event 2365",
                      "https://elgintx.api.civicclerk.com/v1/Events/2365")

        await browser.close()

asyncio.run(main())
