"""Check relationship between event IDs and filestream links in CivicClerk DOM."""

import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        url = "https://www.ci.sherman.tx.us/701/Agendas-and-Minutes"
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)

        # Get all meeting-event list items and check for filestream links inside them
        items = await page.query_selector_all('li.meeting-event, li[class*="meeting-event"]')
        print(f"Meeting event <li> items: {len(items)}")

        for li in items[:8]:
            # Get the event link
            event_link = await li.query_selector('a[href*="portal.civicclerk.com"]')
            if not event_link:
                continue
            text = (await event_link.inner_text()).strip().replace("\n", " ")[:80]
            href = await event_link.get_attribute("href") or ""
            data_id = await event_link.get_attribute("data-id") or ""
            data_date = await event_link.get_attribute("data-date") or ""

            # Check for filestream links inside the same <li>
            fs_links = await li.query_selector_all('a[href*="FileStream"]')

            fs_info = []
            for fs in fs_links:
                fhref = await fs.get_attribute("href") or ""
                fs_info.append(fhref.split("(")[1].split(")")[0] if "(" in fhref else fhref)

            print(f"\n  Event {data_id} ({data_date[:10]}): {text}")
            print(f"    href={href}")
            print(f"    FileStream links inside <li>: {len(fs_links)}")
            for info in fs_info:
                print(f"      {info}")

        await browser.close()

asyncio.run(main())
