"""Quick checks for Dallas, Grand Prairie, Round Rock, Carrollton, Corpus Christi."""
import httpx

c = httpx.Client(follow_redirects=True, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

# 1. DALLAS - Check the actual dataset
print("=== DALLAS ===")
r = c.get("https://www.dallasopendata.com/api/views/e7gq-4sah.json")
print(f"Metadata: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"  Name: {d.get('name')}")
    import datetime
    ts = d.get("rowsUpdatedAt", 0)
    if ts:
        print(f"  Rows updated: {datetime.datetime.fromtimestamp(ts)}")
    cols = d.get("columns", [])
    for col in cols[:8]:
        print(f"  Col: {col.get('fieldName')} ({col.get('dataTypeName')})")

# Get latest records
r2 = c.get("https://www.dallasopendata.com/resource/e7gq-4sah.json",
           params={"$limit": "2", "$order": "issued_date DESC"})
print(f"Data query: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    print(f"  Records: {len(data)}")
    if data:
        print(f"  Keys: {list(data[0].keys())[:10]}")
        print(f"  Latest: {data[0]}")

# 2. Try fetching web pages that returned 403 with different approach
print("\n=== GRAND PRAIRIE ===")
try:
    r = c.get("https://www.gptx.org/Departments/Building-Inspections/Building-Permits-Report",
              headers={"Accept": "text/html,application/xhtml+xml"})
    print(f"Building Permits Report: {r.status_code} (len={len(r.text)})")
    if r.status_code == 200:
        import re
        # Find any links to documents
        links = re.findall(r'href="([^"]*(?:\.pdf|\.xlsx|\.xls|\.csv|DocumentCenter|ViewFile)[^"]*)"', r.text, re.I)
        print(f"  Document links: {links[:10]}")
except Exception as e:
    print(f"  Error: {e}")

# Try GP open data portal
try:
    r = c.get("https://www.gptx.org/city-government/open-data")
    print(f"Open Data page: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# 3. ROUND ROCK
print("\n=== ROUND ROCK ===")
try:
    r = c.get("https://www.roundrocktexas.gov/city-departments/planning-and-development-services/building-inspection/forms-and-reports/",
              headers={"Accept": "text/html,application/xhtml+xml"})
    print(f"Forms page: {r.status_code} (len={len(r.text)})")
    if r.status_code == 200:
        import re
        links = re.findall(r'href="([^"]*(?:\.pdf|\.xlsx|\.xls|\.csv|DocumentCenter|ViewFile)[^"]*)"', r.text, re.I)
        print(f"  Document links: {links[:10]}")
except Exception as e:
    print(f"  Error: {e}")

# Try RR open data
try:
    r = c.get("https://data.roundrocktexas.gov/")
    print(f"Open data portal: {r.status_code}")
except Exception as e:
    print(f"  Open data: {type(e).__name__}")

# 4. CARROLLTON
print("\n=== CARROLLTON ===")
try:
    r = c.get("https://www.cityofcarrollton.com/departments/departments-a-f/building-inspection/building-inspection-reports/archive-permit-reports",
              headers={"Accept": "text/html,application/xhtml+xml"})
    print(f"Archive page: {r.status_code} (len={len(r.text)})")
    if r.status_code == 200:
        import re
        links = re.findall(r'href="([^"]*(?:\.pdf|\.xlsx|\.xls|\.csv|DocumentCenter|ViewFile)[^"]*)"', r.text, re.I)
        print(f"  Document links: {links[:10]}")
except Exception as e:
    print(f"  Error: {e}")

# Also try Carrollton's DocumentCenter
try:
    r = c.get("https://www.cityofcarrollton.com/home/showpublisheddocument?id=0")
    print(f"DocumentCenter test: {r.status_code}")
except Exception as e:
    print(f"  DocumentCenter: {type(e).__name__}")

# 5. CORPUS CHRISTI
print("\n=== CORPUS CHRISTI ===")
# Check the development services applications page
try:
    r = c.get("https://www.corpuschristitx.gov/department-directory/development-services/applications-permits-and-guidance/")
    print(f"Applications page: {r.status_code} (len={len(r.text)})")
    if r.status_code == 200:
        import re
        links = re.findall(r'href="([^"]*(?:permit|report|data|month|fiscal)[^"]*)"', r.text, re.I)
        for l in links[:15]:
            print(f"  {l}")
except Exception as e:
    print(f"  Error: {e}")

# Try CC open data
try:
    r = c.get("https://data.cctexas.com/")
    print(f"CC open data: {r.status_code}")
except Exception as e:
    print(f"  CC open data: {type(e).__name__}")

c.close()
print("\nDone.")
