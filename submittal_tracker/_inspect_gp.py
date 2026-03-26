"""Inspect Grand Prairie permit report page via Playwright."""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(
        "https://www.gptx.org/Departments/Building-Inspections/Building-Permits-Report",
        wait_until="domcontentloaded", timeout=30_000,
    )
    import time; time.sleep(5)
    html = page.content()
    browser.close()

# All href links
all_links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
print(f"Total links: {len(all_links)}")

# Filter for document-like links
for link in all_links:
    low = link.lower()
    if any(ext in low for ext in [".pdf", ".xlsx", ".xls", ".csv", ".doc"]):
        print(f"  DOC: {link}")
    elif any(kw in low for kw in ["permit", "report", "download", "document"]):
        if not any(skip in low for skip in ["css", "js", "font", "image", "style"]):
            print(f"  KW:  {link}")

# Check page text for clues
text = re.sub(r"<[^>]+>", " ", html)
text = re.sub(r"\s+", " ", text).strip()
for seg in text.split("."):
    seg = seg.strip()
    if any(kw in seg.lower() for kw in ["permit", "report", "monthly", "download"]):
        if 20 < len(seg) < 300:
            print(f"  TEXT: {seg}")
