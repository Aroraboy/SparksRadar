"""Inspect Prosper municodemeetings.com P&Z rows."""
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://prosper-tx.municodemeetings.com/",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(5000)

        # Find P&Z rows and their links/dates
        pz_data = await page.evaluate("""() => {
            const rows = document.querySelectorAll('tr, .views-row');
            const pzRows = [];
            for (const row of rows) {
                const title = row.querySelector('.views-field-title');
                if (!title) continue;
                const text = title.innerText.trim().toLowerCase();
                if (text.includes('planning') && text.includes('zoning')) {
                    const cells = row.querySelectorAll('td');
                    const cellTexts = Array.from(cells).map(c => ({
                        cls: c.className.substring(0, 60),
                        text: c.innerText.trim().substring(0, 100)
                    }));
                    const links = Array.from(row.querySelectorAll('a[href]')).map(a => ({
                        text: a.innerText.trim().substring(0, 50),
                        href: a.href.substring(0, 200),
                        cls: a.className.substring(0, 40)
                    }));
                    pzRows.push({
                        titleText: title.innerText.trim(),
                        cells: cellTexts,
                        links
                    });
                }
            }
            return pzRows;
        }""")

        print(f"P&Z rows found: {len(pz_data)}")
        for i, row in enumerate(pz_data[:5]):
            print(f"\n--- P&Z Row {i}: {row['titleText']} ---")
            for cell in row['cells']:
                print(f"  Cell [{cell['cls']}]: {cell['text']}")
            for link in row['links']:
                print(f"  Link [{link['cls']}] '{link['text']}' -> {link['href']}")

        await browser.close()

asyncio.run(inspect())
