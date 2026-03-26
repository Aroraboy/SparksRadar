"""Dallas - try ArcGIS enterprise, ROW permits API, and development services search."""
import httpx
import re

c = httpx.Client(follow_redirects=True, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

# 1. Check ROW permits - these are updated March 2026
print("=== Dallas ROW Permits (Socrata) ===")
for dataset_id in ["xum9-x6px", "bw6g-a3ur"]:
    r = c.get(f"https://www.dallasopendata.com/resource/{dataset_id}.json",
              params={"$limit": "3", "$order": ":id DESC"})
    print(f"  {dataset_id}: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if data:
            print(f"    Keys: {list(data[0].keys())[:10]}")
            print(f"    Sample: {data[0]}")

# 2. Check the sdc_public/CityProperty feature server
print("\n=== Dallas sdc_public/CityProperty ===")
r = c.get("https://gis.dallascityhall.com/arcgis/rest/services/sdc_public/CityProperty/FeatureServer",
          params={"f": "json"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    layers = data.get("layers", [])
    for layer in layers:
        print(f"  Layer {layer['id']}: {layer['name']}")

# 3. Check Pbw_public/ROWMSPermits
print("\n=== Dallas ROWMSPermits ===")
r = c.get("https://gis.dallascityhall.com/arcgis/rest/services/Pbw_public/ROWMSPermits/MapServer",
          params={"f": "json"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    layers = data.get("layers", [])
    for layer in layers:
        print(f"  Layer {layer['id']}: {layer['name']}")

# 4. Try the Dallas development services website directly
print("\n=== Dallas DevServices Website ===")
urls = [
    "https://dallascityhall.com/departments/sustainabledevelopment/Pages/Reports.aspx",
    "https://dallascityhall.com/departments/sustainabledevelopment/buildinginspection/Pages/default.aspx",
]
for url in urls:
    try:
        r = c.get(url)
        print(f"  {url.split('/')[-1]}: {r.status_code}")
        if r.status_code == 200:
            links = re.findall(r'href="([^"]*(?:permit|report|activity|monthly|2026)[^"]*)"', r.text, re.I)
            for l in links[:10]:
                print(f"    {l}")
    except Exception as e:
        print(f"  Error: {e}")

# 5. Try the open data portal for newer building permits-like datasets
print("\n=== Dallas - Search for newer datasets ===")
for keyword in ["permit", "construction", "building inspection"]:
    r = c.get("https://www.dallasopendata.com/api/catalog/v1",
              params={"q": keyword, "limit": 10})
    if r.status_code == 200:
        for result in r.json().get("results", [])[:10]:
            res = result.get("resource", {})
            updated = res.get("data_updated_at", "")
            if "2025" in updated or "2026" in updated:
                print(f"  [{keyword}] {res['name']} | {res['id']} | updated: {updated}")

c.close()
print("\nDone.")
