"""Inspect the Granicus iframe inside Lago Vista's CivicPlus page."""
import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://lagovistatexas.granicus.com/ViewPublisher.php?view_id=1",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(5000)

        # Get all links
        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: a.innerText.trim().substring(0, 120)
            })).filter(l =>
                l.href.toLowerCase().includes('.pdf') ||
                l.href.toLowerCase().includes('agenda') ||
                l.href.toLowerCase().includes('generatedagenda') ||
                l.href.toLowerCase().includes('meeting') ||
                l.text.toLowerCase().includes('agenda') ||
                l.text.toLowerCase().includes('p&z') ||
                l.text.toLowerCase().includes('planning')
            ).slice(0, 40)
        }""")

        print(f"Found {len(links)} relevant links:")
        for l in links:
            print(f"  {l['text'][:80]:80s} | {l['href']}")

        # Also check general page structure
        print("\n--- Page title ---")
        title = await page.title()
        print(f"  {title}")

        # Check for rows / table structure
        rows = await page.evaluate("""() => {
            let rows = document.querySelectorAll('tr, .row, [class*=meeting]');
            return Array.from(rows).slice(0, 10).map(r => r.innerText.trim().substring(0, 200));
        }""")
        print(f"\n--- First {len(rows)} rows ---")
        for r in rows:
            print(f"  {r[:150]}")

        await browser.close()

asyncio.run(check())
