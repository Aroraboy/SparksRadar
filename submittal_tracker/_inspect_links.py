"""Get all download links from the Frisco archive page."""
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

        # Try to find the archive rows with links
        rows = await page.query_selector_all("tr")
        print(f"Total rows: {len(rows)}")
        
        for row in rows:
            text = (await row.inner_text()).strip()
            if not text:
                continue
            links = await row.query_selector_all("a")
            for link in links:
                href = await link.get_attribute("href") or ""
                link_text = (await link.inner_text()).strip()
                if href and ("2025" in link_text or "2026" in link_text or "January" in link_text or "February" in link_text or "March" in link_text):
                    print(f"  {link_text}: {href}")

        # Alternative: get all links on the page
        print("\n\nAll links with dates:")
        all_links = await page.query_selector_all("a")
        for link in all_links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()
            if any(month in text for month in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]):
                full_url = href
                if href.startswith("/"):
                    full_url = "https://www.friscotexas.gov" + href
                print(f"  {text}: {full_url}")

        await browser.close()


asyncio.run(main())
