"""Debug Killeen PDF table extraction."""
import httpx, pdfplumber, io

r = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}).get(
    "https://www.killeentexas.gov/DocumentCenter/View/7781/Monthly-Permit-Report-PDF"
)
pdf = pdfplumber.open(io.BytesIO(r.content))
print(f"Pages: {len(pdf.pages)}")

# Check first 3 pages
for pi in range(min(5, len(pdf.pages))):
    pg = pdf.pages[pi]
    tables = pg.extract_tables()
    print(f"\n=== Page {pi+1}: {len(tables)} tables ===")
    for ti, tbl in enumerate(tables):
        print(f"  Table {ti}: {len(tbl)} rows x {len(tbl[0]) if tbl else 0} cols")
        for ri, row in enumerate(tbl[:8]):
            print(f"    Row {ri}: {[str(c)[:40] if c else 'None' for c in row]}")
