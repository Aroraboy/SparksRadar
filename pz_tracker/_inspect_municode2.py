"""Inspect Prosper municodemeetings.com in detail."""
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
        
        # Get meeting items with their context
        items = await page.evaluate("""() => {
            const results = [];
            // Find all meeting sections/items
            const meetingItems = document.querySelectorAll('.meeting-item, .views-row, .node, [class*="meeting"]');
            for (const item of Array.from(meetingItems).slice(0, 15)) {
                const text = item.innerText.trim().substring(0, 200);
                const cls = item.className;
                const links = Array.from(item.querySelectorAll('a[href]')).map(a => ({
                    text: a.innerText.trim().substring(0, 50),
                    href: a.href.substring(0, 150)
                }));
                if (text.length > 10) results.push({cls: cls.substring(0, 60), text, links});
            }
            return results;
        }""")
        
        print(f"Meeting items found: {len(items)}")
        for i, item in enumerate(items[:10]):
            print(f"\n--- Item {i} [{item['cls']}] ---")
            print(f"  Text: {item['text'][:150]}")
            for link in item['links'][:5]:
                print(f"  Link: [{link['text']}] -> {link['href']}")

        # Also check the headings/titles for P&Z meeting names
        headings = await page.evaluate("""() => {
            const els = document.querySelectorAll('h1, h2, h3, h4, .field-content, .views-field-title, .meeting-title');
            return Array.from(els).slice(0, 20).map(e => ({
                tag: e.tagName,
                cls: e.className.substring(0, 40),
                text: e.innerText.trim().substring(0, 100)
            }));
        }""")
        print(f"\n=== Headings/Titles ({len(headings)}) ===")
        for h in headings:
            if h['text']:
                print(f"  {h['tag']}.{h['cls']}: {h['text']}")

        await browser.close()

asyncio.run(inspect())
