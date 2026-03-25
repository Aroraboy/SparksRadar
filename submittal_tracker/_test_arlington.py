"""Quick test for Arlington date query."""
import httpx

base = "https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1/query"
tests = [
    "ISSUEDATE >= '2026-01-01'",
    "ISSUEDATE >= DATE '2026-01-01'",
    "ISSUEDATE >= TIMESTAMP '2026-01-01 00:00:00'",
    "ISSUEDATE >= 1735689600000",
]
for w in tests:
    r = httpx.get(base, params={"where": w, "returnCountOnly": "true", "f": "json"},
                  follow_redirects=True, timeout=15)
    print(f"{w!r} => {r.text[:200]}")
