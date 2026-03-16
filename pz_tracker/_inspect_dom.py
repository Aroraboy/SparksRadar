"""Test CivicClerk file download and DOM structure."""

import asyncio
import httpx
from playwright.async_api import async_playwright


async def test_download():
    """Test direct download of CivicClerk FileStream URL."""
    url = "https://SHERMANTX.api.civicclerk.com/v1/Meetings/GetMeetingFileStream(fileId=2384,plainText=false)"
    print(f"Testing direct download: {url}")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, timeout=15)
        print(f"  Status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('content-type', 'N/A')}")
        print(f"  Content-Length: {len(resp.content)} bytes")
        print(f"  First 20 bytes: {resp.content[:20]}")


async def inspect_dom():
    """Check DOM structure of how FileStream links relate to event entries."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.ci.sherman.tx.us/701/Agendas-and-Minutes"
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Find the widget container and dump its structure
        # Look for P&Z event entries and nearby filestream links
        pz_links = await page.query_selector_all('a[href*="portal.civicclerk.com/event"]')
        print(f"\nP&Z event links on main page: {len(pz_links)}")

        for a in pz_links[:5]:
            href = await a.get_attribute("href") or ""
            text = (await a.inner_text()).strip().replace("\n", " ")[:100]
            if "planning" in text.lower() or "zoning" in text.lower():
                print(f"\n  P&Z link: {href}")
                print(f"    Text: {text}")

                # Find parent container and look for sibling filestream links
                parent_html = await a.evaluate("""el => {
                    // Go up a few levels to find the meeting entry container
                    let container = el.closest('[class*="event"], [class*="meeting"], [class*="item"], li, tr') || el.parentElement.parentElement;
                    return container ? container.outerHTML.substring(0, 2000) : 'no container';
                }""")
                print(f"    Parent HTML:\n{parent_html[:1000]}")

        await browser.close()

async def main():
    await test_download()
    await inspect_dom()

asyncio.run(main())
