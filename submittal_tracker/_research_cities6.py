"""Quick targeted checks for remaining cities."""
import httpx
import re

c = httpx.Client(follow_redirects=True, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

# 1. CORPUS CHRISTI - reports page
print("=== CC REPORTS ===")
r = c.get("https://www.corpuschristitx.gov/department-directory/development-services/reports/")
print(f"Status: {r.status_code}, len={len(r.text)}")
if r.status_code == 200:
    links = re.findall(r'href="([^"]*(?:permit|report|fiscal|month|2026|2025)[^"]*)"', r.text, re.I)
    for l in links[:20]:
        print(f"  {l}")
    dl = re.findall(r'href="([^"]*\.(?:pdf|xlsx|xls|csv))"', r.text, re.I)
    for d in dl[:10]:
        print(f"  DL: {d}")

# 2. DALLAS - GIS Enterprise
print("\n=== DALLAS GIS ===")
try:
    r = c.get("https://gis.dallascityhall.com/arcgis/rest/services", params={"f": "json"})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        folders = data.get("folders", [])
        print(f"Folders: {folders}")
        for svc in data.get("services", []):
            n = svc.get("name", "").lower()
            if any(k in n for k in ["permit", "build", "develop", "plan", "construct"]):
                print(f"  SVC: {svc}")
except Exception as e:
    print(f"Error: {e}")

# Check Dev Services folder if exists
for folder in ["DevServices", "Development", "Planning", "DBI"]:
    try:
        r = c.get(f"https://gis.dallascityhall.com/arcgis/rest/services/{folder}",
                  params={"f": "json"})
        if r.status_code == 200:
            data = r.json()
            svcs = data.get("services", [])
            if svcs:
                print(f"\n  Folder '{folder}':")
                for svc in svcs:
                    print(f"    {svc['name']} | {svc['type']}")
    except:
        pass

# 3. Also try Dallas open data API - maybe different resource ID
print("\n=== DALLAS - Alternate Datasets ===")
# Try the Bid Data dataset
r = c.get("https://www.dallasopendata.com/resource/irab-qmty.json",
          params={"$limit": "2", "$order": ":id DESC"})
print(f"Bid Data: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if data:
        print(f"  Keys: {list(data[0].keys())[:10]}")
        print(f"  Sample: {data[0]}")

c.close()
print("\nDone.")
