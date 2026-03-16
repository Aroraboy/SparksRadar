"""Quick inspection script for CivicPlus page structure."""
import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://tx-lagovista.civicplus.com/368/Agendas-Minutes-After-April-2023",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(5000)

        links = await page.evaluate("""() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: a.innerText.trim().substring(0, 120)
            })).filter(l =>
                l.text.toLowerCase().includes('agenda') ||
                l.href.toLowerCase().includes('agenda') ||
                l.href.toLowerCase().includes('.pdf') ||
                l.href.toLowerCase().includes('viewfile') ||
                l.href.toLowerCase().includes('agendacenter')
            ).slice(0, 40)
        }""")

        for l in links:
            print(f"{l['text'][:80]:80s} | {l['href']}")

        print("\n--- iframe check ---")
        iframes = await page.query_selector_all("iframe")
        print(f"Found {len(iframes)} iframe(s)")
        for iframe in iframes:
            src = await iframe.get_attribute("src")
            print(f"  iframe src: {src}")

        await browser.close()

asyncio.run(check())
