"""Research remaining city APIs: Dallas, Corpus Christi, Grand Prairie, Round Rock, Carrollton."""
import httpx
import re

client = httpx.Client(follow_redirects=True, timeout=30, headers={"User-Agent": "Mozilla/5.0"})

# 1. Dallas Socrata - Building Permits (e7gq-4sah)
print("=" * 60)
print("DALLAS - Socrata Building Permits")
try:
    r = client.get(
        "https://www.dallasopendata.com/resource/e7gq-4sah.json",
        params={
            "$where": "issued_date >= '2026-01-01T00:00:00'",
            "$limit": "3",
            "$order": "issued_date DESC",
        },
    )
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"  Rows returned: {len(data)}")
        if data:
            print(f"  Keys: {list(data[0].keys())}")
            print(f"  Sample: {data[0]}")
    else:
        print(f"  Error: {r.text[:300]}")
except Exception as e:
    print(f"  Exception: {e}")

# Also try getting just the count
try:
    r = client.get(
        "https://www.dallasopendata.com/resource/e7gq-4sah.json",
        params={
            "$where": "issued_date >= '2026-01-01T00:00:00'",
            "$select": "count(*) as cnt",
        },
    )
    if r.status_code == 200:
        print(f"  Total 2026 count: {r.json()}")
except Exception as e:
    print(f"  Count error: {e}")

# 2. Corpus Christi - check for open data / Socrata
print("\n" + "=" * 60)
print("CORPUS CHRISTI - Open Data")
for url in [
    "https://www.cctexas.com/departments/development-services/reports",
    "https://www.corpuschristitx.gov/department:directory/development:services/reports/fiscal:permit:history:reports:by:month/",
]:
    try:
        r = client.get(url)
        print(f"  {url[:80]}... => {r.status_code}")
        if r.status_code == 200 and len(r.text) > 100:
            links = re.findall(r'href=["\']([^"\']*(?:permit|report|2026)[^"\']*)["\']', r.text, re.I)
            if links:
                print(f"  Found {len(links)} relevant links:")
                for l in links[:15]:
                    print(f"    {l}")
    except Exception as e:
        print(f"  {url[:80]}... => {e}")

# Socrata catalog search for CC
try:
    r = client.get("https://api.us.socrata.com/api/catalog/v1",
        params={"q": "permits corpus christi texas", "limit": 5})
    if r.status_code == 200:
        for result in r.json().get("results", [])[:5]:
            res = result.get("resource", {})
            dom = result.get("metadata", {}).get("domain", "")
            print(f"  Socrata: [{dom}] {res.get('name','')} | {res.get('id','')}")
except:
    pass

# 3. Grand Prairie
print("\n" + "=" * 60)
print("GRAND PRAIRIE")
try:
    r = client.get("https://www.gptx.org/Departments/Building-Inspections/Building-Permits-Report")
    print(f"  Building Permits Report page: {r.status_code}")
    if r.status_code == 200:
        links = re.findall(r'href=["\']([^"\']*(?:permit|report|building)[^"\']*\.(?:xlsx|xls|pdf|csv))["\']', r.text, re.I)
        if links:
            print(f"  Download links: {links[:10]}")
        links2 = re.findall(r'href=["\']([^"\']*2026[^"\']*)["\']', r.text, re.I)
        if links2:
            print(f"  2026 links: {links2[:10]}")
        # Show page snippet
        import html
        text = re.sub(r'<[^>]+>', ' ', r.text)
        text = re.sub(r'\s+', ' ', text)
        for kw in ['2026', '2025', 'permit', 'report', 'download']:
            idx = text.lower().find(kw)
            if idx >= 0:
                print(f"  Context for '{kw}': ...{text[max(0,idx-80):idx+80]}...")
except Exception as e:
    print(f"  Error: {e}")

# ArcGIS Hub search for Grand Prairie
try:
    r = client.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": "permits grand prairie texas", "page[size]": 5})
    if r.status_code == 200:
        for item in r.json().get("data", [])[:5]:
            attrs = item.get("attributes", {})
            print(f"  Hub: {attrs.get('name','')} | org={attrs.get('organization','')} | {attrs.get('url','')[:80]}")
except:
    pass

# 4. Round Rock
print("\n" + "=" * 60)
print("ROUND ROCK")
try:
    r = client.get("https://www.roundrocktexas.gov/city-departments/planning-and-development-services/building-inspection/forms-and-reports/")
    print(f"  Forms page: {r.status_code}")
    if r.status_code == 200:
        links = re.findall(r'href=["\']([^"\']*\.(?:xlsx|xls|pdf|csv))["\']', r.text, re.I)
        if links:
            print(f"  Download links ({len(links)}): {links[:10]}")
        links2 = re.findall(r'href=["\']([^"\']*2026[^"\']*)["\']', r.text, re.I)
        if links2:
            print(f"  2026 links: {links2[:10]}")
        text = re.sub(r'<[^>]+>', ' ', r.text)
        text = re.sub(r'\s+', ' ', text)
        for kw in ['2026', 'permit', 'report', 'monthly']:
            idx = text.lower().find(kw)
            if idx >= 0:
                print(f"  Context for '{kw}': ...{text[max(0,idx-80):idx+80]}...")
                break
except Exception as e:
    print(f"  Error: {e}")

# ArcGIS Hub search for Round Rock
try:
    r = client.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": "permits round rock texas", "page[size]": 5})
    if r.status_code == 200:
        for item in r.json().get("data", [])[:5]:
            attrs = item.get("attributes", {})
            print(f"  Hub: {attrs.get('name','')} | org={attrs.get('organization','')} | {attrs.get('url','')[:80]}")
except:
    pass

# 5. Carrollton
print("\n" + "=" * 60)
print("CARROLLTON")
try:
    r = client.get("https://www.cityofcarrollton.com/departments/departments-a-f/building-inspection/building-inspection-reports/archive-permit-reports")
    print(f"  Archive page: {r.status_code}")
    if r.status_code == 200:
        links = re.findall(r'href=["\']([^"\']*(?:permit|report|2026)[^"\']*)["\']', r.text, re.I)
        if links:
            print(f"  Relevant links ({len(links)}):")
            for l in links[:15]:
                print(f"    {l}")
        dl = re.findall(r'href=["\']([^"\']*\.(?:xlsx|xls|pdf|csv))["\']', r.text, re.I)
        if dl:
            print(f"  Download links: {dl[:10]}")
except Exception as e:
    print(f"  Error: {e}")

# ArcGIS Hub search for Carrollton
try:
    r = client.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": "permits carrollton texas", "page[size]": 5})
    if r.status_code == 200:
        for item in r.json().get("data", [])[:5]:
            attrs = item.get("attributes", {})
            print(f"  Hub: {attrs.get('name','')} | org={attrs.get('organization','')} | {attrs.get('url','')[:80]}")
except:
    pass

client.close()
print("\nDone.")
