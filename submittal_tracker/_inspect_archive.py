"""Inspect the Frisco archive page for submittal tracker documents."""
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://www.friscotexas.gov/Archive.aspx?AMID=81",
            timeout=20000,
            wait_until="networkidle",
        )

        # Get all links containing ViewFile or ArchiveCenter
        links = await page.query_selector_all("a")
        print("All relevant links:")
        for link in links:
            text = (await link.inner_text()).strip()
            href = await link.get_attribute("href") or ""
            if "ViewFile" in href or "ArchiveCenter" in href or "Item" in href:
                print(f"  {text}: {href}")

        # Check for year/category structure
        selects = await page.query_selector_all("select")
        for sel in selects:
            sel_id = await sel.get_attribute("id") or ""
            options = await sel.query_selector_all("option")
            print(f"\nSelect '{sel_id}':")
            for opt in options[:10]:
                val = await opt.get_attribute("value") or ""
                txt = (await opt.inner_text()).strip()
                print(f"  {val}: {txt}")

        # Check the main content area
        content_area = await page.query_selector(".archiveDocuments, .archive-list, #ctl00_ContentPlaceHolder1_ArchiveListPanel")
        if content_area:
            inner = await content_area.inner_text()
            print(f"\nContent area text (first 1000):\n{inner[:1000]}")
        else:
            # Try broader content
            body_text = await page.inner_text("body")
            # Filter for relevant lines
            for line in body_text.split("\n"):
                line = line.strip()
                if line and ("submittal" in line.lower() or "2026" in line or "2025" in line or "tracker" in line.lower()):
                    print(f"  {line}")

        await browser.close()


asyncio.run(main())
