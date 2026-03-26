"""Check for additional months of data."""
import httpx
client = httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})

# Carrollton - pattern: MM_DD_YY THRU MM_DD_YY
for m, d in [("01_01_26", "01_31_26"), ("03_01_26", "03_31_26")]:
    url = f"https://webrpts.cityofcarrollton.com/bldg_insp/results/permit_reports/archive/{m}%20THRU%20{d}.pdf"
    r = client.get(url)
    print(f"Carrollton {m}: {r.status_code}, {len(r.content)} bytes")

# Killeen - try nearby DocumentCenter IDs for Jan report
for vid in [7717, 7718, 7719, 7750, 7780, 7782]:
    url = f"https://www.killeentexas.gov/DocumentCenter/View/{vid}/Monthly-Permit-Report-PDF"
    r = client.get(url)
    ct = r.headers.get("content-type", "?")[:40]
    print(f"Killeen {vid}: {r.status_code}, ct={ct}, {len(r.content)} bytes")

# Brownsville - try nearby IDs for Jan
for vid in [17468, 17469, 17470, 17530, 17532]:
    url = f"https://www.brownsvilletx.gov/DocumentCenter/View/{vid}"
    r = client.get(url)
    ct = r.headers.get("content-type", "?")[:40]
    print(f"Brownsville {vid}: {r.status_code}, ct={ct}, {len(r.content)} bytes")
