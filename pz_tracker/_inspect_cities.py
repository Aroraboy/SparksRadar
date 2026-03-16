"""Quick inspection script: dump iframes and key links for Sherman, Elgin, Victoria."""

import asyncio
from playwright.async_api import async_playwright

CITIES = {
    "Sherman": "https://www.ci.sherman.tx.us/701/Agendas-and-Minutes",
    "Elgin":   "https://www.elgintexas.gov/129/Agendas-Minutes",
    "Victoria": "https://victoriatx.civicweb.net/Portal/MeetingInformation.aspx?Id=491",
}


async def inspect(name, url, browser):
    print(f"\n{'='*60}\n  {name} — {url}\n{'='*60}")
    page = await browser.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
        await page.wait_for_timeout(5000)

        # Iframes
        iframes = await page.query_selector_all("iframe")
        print(f"\n  Iframes ({len(iframes)}):")
        for i, ifr in enumerate(iframes):
            src = await ifr.get_attribute("src") or "(no src)"
            print(f"    [{i}] {src}")

        # All links
        links = await page.query_selector_all("a[href]")
        print(f"\n  Links ({len(links)} total) — showing PDF and agenda-related:")
        shown = 0
        for a in links:
            href = (await a.get_attribute("href")) or ""
            text = (await a.inner_text()).strip().replace("\n", " ")[:80]
            hl = href.lower()
            tl = text.lower()
            if ".pdf" in hl or "agenda" in tl or "agenda" in hl or "planning" in tl or "zoning" in tl or "p&z" in tl or "filestream" in hl:
                print(f"    href={href}")
                print(f"      text={text}")
                shown += 1
        if shown == 0:
            print("    (none found — showing first 30 links)")
            for a in links[:30]:
                href = (await a.get_attribute("href")) or ""
                text = (await a.inner_text()).strip().replace("\n", " ")[:80]
                print(f"    href={href}  text={text}")

    except Exception as e:
        print(f"  ERROR: {e}")
    finally:
        await page.close()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for name, url in CITIES.items():
            await inspect(name, url, browser)
        await browser.close()

asyncio.run(main())
