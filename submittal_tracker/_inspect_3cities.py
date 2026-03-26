"""Inspect Carrollton, Killeen, Brownsville PDFs to understand structure."""
import httpx, pdfplumber, io

PDFS = {
    "Carrollton": "https://webrpts.cityofcarrollton.com/bldg_insp/results/permit_reports/archive/02_01_26%20THRU%2002_28_26.pdf",
    "Killeen": "https://www.killeentexas.gov/DocumentCenter/View/7781/Monthly-Permit-Report-PDF",
    "Brownsville": "https://www.brownsvilletx.gov/DocumentCenter/View/17531/February-2026-Permits",
}

client = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})

for city, url in PDFS.items():
    print(f"\n{'='*70}")
    print(f"{city}: {url}")
    try:
        resp = client.get(url)
        print(f"Status: {resp.status_code}, Size: {len(resp.content)} bytes, CT: {resp.headers.get('content-type','?')}")
        if resp.status_code != 200:
            print(f"  FAILED: {resp.text[:300]}")
            continue
        pdf = pdfplumber.open(io.BytesIO(resp.content))
        print(f"Pages: {len(pdf.pages)}")
        for i, pg in enumerate(pdf.pages[:3]):
            text = pg.extract_text() or ""
            print(f"\n--- Page {i+1} text (first 1000 chars) ---")
            print(text[:1000])
            tables = pg.extract_tables()
            if tables:
                print(f"\n--- Page {i+1} tables: {len(tables)} ---")
                for ti, tbl in enumerate(tables[:2]):
                    print(f"  Table {ti}: {len(tbl)} rows x {len(tbl[0]) if tbl else 0} cols")
                    for row in tbl[:5]:
                        print(f"    {row}")
    except Exception as e:
        print(f"  ERROR: {e}")
