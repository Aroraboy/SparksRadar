"""Inspect Round Rock PDF reports to understand structure."""
from playwright.sync_api import sync_playwright
import pdfplumber, io

urls = [
    "https://www.roundrocktexas.gov/wp-content/uploads/2026/02/January-2026-Monthly-Report.pdf",
    "https://www.roundrocktexas.gov/wp-content/uploads/2026/02/January-2026-Periodic-Report.pdf",
]
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto("https://www.roundrocktexas.gov", wait_until="domcontentloaded", timeout=15000)

    for url in urls:
        print(f"\n{'='*60}")
        print(f"URL: {url.split('/')[-1]}")
        resp = ctx.request.get(url)
        print(f"Status: {resp.status}, Size: {len(resp.body())} bytes")
        if resp.status == 200:
            body = resp.body()
            try:
                pdf = pdfplumber.open(io.BytesIO(body))
                print(f"Pages: {len(pdf.pages)}")
                for i, pg in enumerate(pdf.pages[:3]):
                    text = pg.extract_text() or ""
                    print(f"\n--- Page {i+1} text (first 800 chars) ---")
                    print(text[:800])
                    tables = pg.extract_tables()
                    if tables:
                        print(f"\n--- Page {i+1} tables: {len(tables)} ---")
                        for ti, tbl in enumerate(tables[:2]):
                            print(f"  Table {ti}: {len(tbl)} rows")
                            for row in tbl[:5]:
                                print(f"    {row}")
            except Exception as e:
                print(f"Error parsing: {e}")
    browser.close()
