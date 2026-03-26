"""Inspect Carrollton permit reports page via Playwright."""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context()
    page = ctx.new_page()
    page.goto(
        "https://www.cityofcarrollton.com/departments/departments-a-f/building-inspection/building-inspection-reports/archive-permit-reports",
        wait_until="domcontentloaded", timeout=30_000,
    )
    page.wait_for_timeout(3000)
    html = page.content()
    browser.close()

print(f"HTML length: {len(html)}")

# All links
all_links = re.findall(r'href=["\']([^"\']+)["\']', html, re.I)
print(f"Total links: {len(all_links)}")

# Document links
for link in all_links:
    low = link.lower()
    if any(ext in low for ext in [".pdf", ".xlsx", ".xls", ".csv", ".doc"]):
        print(f"  DOC: {link}")

# Links containing permit/report keywords
for link in all_links:
    low = link.lower()
    if any(kw in low for kw in ["permit", "report", "archive", "download"]):
        if not any(skip in low for skip in [".css", ".js", "font", "style", "script"]):
            print(f"  KW: {link}")

# 2026 links
for link in all_links:
    if "2026" in link or "26" in link.split("/")[-1]:
        print(f"  2026: {link}")

# Text content
text = re.sub(r"<[^>]+>", " ", html)
text = re.sub(r"\s+", " ", text).strip()
for seg in text.split("."):
    seg = seg.strip()
    if any(kw in seg.lower() for kw in ["permit", "report", "archive", "2026", "2025"]):
        if 20 < len(seg) < 300:
            print(f"  TEXT: {seg}")
