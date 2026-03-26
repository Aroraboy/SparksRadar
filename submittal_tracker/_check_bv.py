"""Quick check Brownsville Jan URL."""
import httpx
r = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}).get(
    "https://www.brownsvilletx.gov/DocumentCenter/View/17424/January-2026-Permits"
)
ct = r.headers.get("content-type", "?")
print(f"Status: {r.status_code}, CT: {ct[:40]}, Size: {len(r.content)}")
