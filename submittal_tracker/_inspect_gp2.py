"""Inspect Grand Prairie external permits report portal."""
from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(
        "https://ravingfans.gptx.org/GPTX/EconomicDevelopment/PermitsReport/",
        wait_until="domcontentloaded", timeout=30_000,
    )
    import time; time.sleep(5)
    html = page.content()
    browser.close()

print(f"HTML length: {len(html)}")
# Look for any data table, iframe, or report content
iframes = re.findall(r'<iframe[^>]*src=["\']([^"\']*)["\']', html, re.I)
if iframes:
    print(f"Iframes: {iframes}")

# Extract text
text = re.sub(r"<[^>]+>", " ", html)
text = re.sub(r"\s+", " ", text).strip()
print(f"Text length: {len(text)}")
# Print first 2000 chars of text
print(text[:2000])
