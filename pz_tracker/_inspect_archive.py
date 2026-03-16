"""Inspect Midlothian Archive.aspx page."""
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(
            "https://www.midlothian.tx.us/Archive.aspx?AMID=32",
            wait_until="domcontentloaded", timeout=30000,
        )
        await page.wait_for_timeout(5000)

        # Check if there are iframes
        iframes = await page.query_selector_all("iframe")
        print(f"Iframes: {len(iframes)}")
        for f in iframes:
            src = await f.get_attribute("src") or ""
            print(f"  iframe src: {src[:150]}")

        # Check for links
        data = await page.evaluate("""() => {
            const links = document.querySelectorAll('a[href]');
            const results = [];
            for (const a of links) {
                const href = a.href;
                const text = a.innerText.trim().substring(0, 60);
                if (href.includes('.pdf') || href.includes('Archive') || href.includes('agenda') || href.includes('ViewFile')) {
                    results.push({text, href: href.substring(0, 200)});
                }
            }
            return results;
        }""")
        print(f"\nRelevant links: {len(data)}")
        for d in data[:20]:
            print(f"  [{d['text']}] -> {d['href']}")

        # Check for table rows
        rows = await page.query_selector_all("tr")
        print(f"\nTable rows: {len(rows)}")
        pz_rows = []
        for r in rows:
            rt = (await r.inner_text()).strip().lower()
            if "p&z" in rt or "planning" in rt or "zoning" in rt:
                links = await r.query_selector_all("a[href]")
                link_data = []
                for a in links:
                    href = await a.get_attribute("href") or ""
                    text = (await a.inner_text()).strip()
                    link_data.append(f"  [{text}]({href[:100]})")
                pz_rows.append({"text": (await r.inner_text())[:200], "links": link_data})

        print(f"P&Z rows: {len(pz_rows)}")
        for pr in pz_rows[:5]:
            print(f"  Text: {pr['text']}")
            for lnk in pr['links']:
                print(f"    {lnk}")

        await browser.close()

asyncio.run(inspect())
