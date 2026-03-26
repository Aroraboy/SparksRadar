"""Check Brownsville PDF with alternative extraction methods."""
import httpx, pdfplumber, io, re

r = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}).get(
    "https://www.brownsvilletx.gov/DocumentCenter/View/17531/February-2026-Permits"
)
pdf = pdfplumber.open(io.BytesIO(r.content))
print(f"Pages: {len(pdf.pages)}")

pg = pdf.pages[0]
# Try extracting words
words = pg.extract_words()
print(f"Words on page 1: {len(words)}")
for w in words[:20]:
    print(f"  '{w['text']}'")

# Check chars
chars = pg.chars
print(f"\nChars on page 1: {len(chars)}")
for c in chars[:20]:
    print(f"  fontname={c.get('fontname','?')} text='{c['text']}'")

# Check if it's an image-based PDF (scanned)
images = pg.images
print(f"\nImages on page 1: {len(images)}")
