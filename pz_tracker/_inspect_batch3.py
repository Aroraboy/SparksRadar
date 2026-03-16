"""Inspect Grapevine and Plano more deeply."""
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
logging.basicConfig(level=logging.WARNING, format="%(levelname)s  %(message)s")

async def inspect(city, url):
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(5000)

            # Get all table rows with text
            rows = await page.evaluate("""() => {
                const rows = document.querySelectorAll('tr');
                const results = [];
                for (const r of rows) {
                    const t = r.innerText.trim();
                    if (t.length > 5 && t.length < 300) {
                        const links = Array.from(r.querySelectorAll('a[href]')).map(a => ({
                            text: a.innerText.trim().substring(0, 50),
                            href: a.href.substring(0, 120)
                        }));
                        results.push({text: t.substring(0, 150), links, cls: r.className.substring(0, 40)});
                    }
                }
                return results.slice(0, 20);
            }""")

            print(f"\n=== {city} ({url[:50]}) ===")
            pz_found = False
            for i, r in enumerate(rows[:20]):
                text_low = r['text'].lower()
                if 'planning' in text_low or 'zoning' in text_low or 'p&z' in text_low or 'p & z' in text_low:
                    pz_found = True
                    print(f"  ROW {i} [P&Z]: {r['text'][:120]}")
                    for l in r['links'][:5]:
                        print(f"    Link: [{l['text']}] -> {l['href']}")

            if not pz_found:
                print("  No P&Z rows found. First 5 rows:")
                for r in rows[:5]:
                    print(f"  [{r['cls']}] {r['text'][:100]}")
                    for l in r['links'][:3]:
                        print(f"    [{l['text']}] -> {l['href']}")

        except Exception as e:
            print(f"\n=== {city} ===\n  ERR: {str(e)[:100]}")
        finally:
            await browser.close()

async def main():
    await inspect("Grapevine", "https://www.grapevinetexas.gov/89/Agendas-Minutes")
    await inspect("Plano", "https://www.plano.gov/1251/Planning-Zoning-Commission-Agendas-Minut")
    await inspect("Trophy Club", "https://www.trophyclub.org/809/Agendas-and-Minutes")

asyncio.run(main())
