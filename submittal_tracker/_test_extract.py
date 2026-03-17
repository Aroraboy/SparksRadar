"""Quick test of the submittal tracker pipeline."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from submittal_tracker.scraper import discover_documents
from submittal_tracker.extractor import download_pdf, extract_from_pdf


async def test():
    # 1. Test discovery
    docs = await discover_documents(
        "https://www.friscotexas.gov/Archive.aspx?AMID=81",
        "https://www.friscotexas.gov",
        "https://www.friscotexas.gov/ArchiveCenter/ViewFile/Item/{adid}",
        year_filter=2026,
    )
    print(f"Discovered {len(docs)} documents (2026+):")
    for d in docs:
        date_str = d.parsed_date.strftime("%Y-%m-%d")
        print(f"  {d.date_label:25s}  ADID={d.adid}  date={date_str}")

    # 2. Test extraction on first document
    if docs:
        doc = docs[0]
        date_str = doc.parsed_date.strftime("%Y-%m-%d")
        print(f"\nDownloading first doc: {doc.pdf_url}")
        pdf_bytes = download_pdf(doc.pdf_url)
        if pdf_bytes:
            print(f"  PDF size: {len(pdf_bytes)} bytes")
            rows = extract_from_pdf(pdf_bytes, doc.pdf_url, date_str)
            print(f"  Extracted {len(rows)} rows:")
            for r in rows:
                print(f"    {r.case_number:12s} | {r.project_type:25s} | {r.address[:45]:45s} | {r.lead_priority}")


asyncio.run(test())
