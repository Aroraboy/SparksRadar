"""Deeper research for remaining cities."""
import httpx

c = httpx.Client(follow_redirects=True, timeout=20, headers={"User-Agent": "Mozilla/5.0"})

# 1. DALLAS - ArcGIS Hub search for Dallas-org datasets
print("=== DALLAS - ArcGIS Hub ===")
r = c.get("https://hub.arcgis.com/api/v3/datasets",
    params={"q": "building permits dallas texas", "page[size]": 10})
for item in r.json().get("data", [])[:10]:
    a = item.get("attributes", {})
    org = a.get("organization", "")
    if "dallas" in org.lower():
        print(f"  {a['name']} | org={org} | {a.get('url', '')[:100]}")

# Also check for "issued permits" or "construction"
for query in ["issued permits dallas", "construction permits dallas", "certificate occupancy dallas"]:
    r = c.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": query, "page[size]": 5})
    for item in r.json().get("data", [])[:5]:
        a = item.get("attributes", {})
        org = a.get("organization", "")
        if "dallas" in org.lower():
            print(f"  [{query}] {a['name']} | {a.get('url', '')[:100]}")

# 2. ROUND ROCK - ArcGIS services
print("\n=== ROUND ROCK - ArcGIS services ===")
try:
    r = c.get("https://maps.roundrocktexas.gov/arcgis/rest/services", params={"f": "json"})
    data = r.json()
    print(f"  Folders: {data.get('folders', [])}")
    for svc in data.get("services", []):
        print(f"  {svc['name']} | {svc['type']}")
except Exception as e:
    print(f"  Error: {e}")

# Check subfolders
for folder in ["Planning", "Development", "Building", "Permits", "OpenData"]:
    try:
        r = c.get(f"https://maps.roundrocktexas.gov/arcgis/rest/services/{folder}",
            params={"f": "json"})
        if r.status_code == 200:
            data = r.json()
            for svc in data.get("services", []):
                print(f"  [{folder}] {svc['name']} | {svc['type']}")
    except:
        pass

# Also search ArcGIS Hub specifically
r = c.get("https://hub.arcgis.com/api/v3/datasets",
    params={"q": "permits round rock", "page[size]": 10})
for item in r.json().get("data", [])[:10]:
    a = item.get("attributes", {})
    org = a.get("organization", "")
    if "round rock" in org.lower():
        print(f"  Hub: {a['name']} | {a.get('url', '')[:100]}")

# 3. GRAND PRAIRIE - try various GIS servers
print("\n=== GRAND PRAIRIE - GIS ===")
gp_bases = [
    "https://gis.gptx.org/arcgis/rest/services",
    "https://gismaps.gptx.org/arcgis/rest/services",
    "https://maps.gptx.org/arcgis/rest/services",
    "https://services.arcgis.com/",  # skip
]
for base in gp_bases[:3]:
    try:
        r = c.get(base, params={"f": "json"})
        print(f"  {base}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            folders = data.get("folders", [])
            print(f"    Folders: {folders}")
            for svc in data.get("services", []):
                print(f"    {svc['name']} | {svc['type']}")
    except Exception as e:
        print(f"  {base}: {type(e).__name__}")

# Try Hub search
for query in ["permits grand prairie", "building grand prairie texas"]:
    r = c.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": query, "page[size]": 5})
    for item in r.json().get("data", [])[:5]:
        a = item.get("attributes", {})
        org = a.get("organization", "")
        if "grand prairie" in org.lower() or "gptx" in org.lower():
            print(f"  Hub [{query}]: {a['name']} | {a.get('url', '')[:100]}")

# 4. CARROLLTON
print("\n=== CARROLLTON - GIS ===")
for base in [
    "https://gis.cityofcarrollton.com/arcgis/rest/services",
    "https://maps.cityofcarrollton.com/arcgis/rest/services",
]:
    try:
        r = c.get(base, params={"f": "json"})
        print(f"  {base}: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            folders = data.get("folders", [])
            print(f"    Folders: {folders}")
    except Exception as e:
        print(f"  {base}: {type(e).__name__}")

# Try Hub
for query in ["permits carrollton texas", "building carrollton"]:
    r = c.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": query, "page[size]": 5})
    for item in r.json().get("data", [])[:5]:
        a = item.get("attributes", {})
        org = a.get("organization", "")
        if "carrollton" in org.lower():
            print(f"  Hub: {a['name']} | {a.get('url', '')[:100]}")

# 5. Check Corpus Christi development services page more carefully
print("\n=== CORPUS CHRISTI - Development Services ===")
try:
    r = c.get("https://www.cctexas.com/departments/development-services")
    if r.status_code == 200:
        import re
        links = re.findall(r'href=["\']([^"\']*(?:permit|report|data|open)[^"\']*)["\']', r.text, re.I)
        for l in links[:20]:
            print(f"  {l}")
except Exception as e:
    print(f"  Error: {e}")

# CC ArcGIS Hub
for query in ["permits corpus christi", "building permits cctexas"]:
    r = c.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": query, "page[size]": 5})
    for item in r.json().get("data", [])[:5]:
        a = item.get("attributes", {})
        org = a.get("organization", "")
        if "corpus" in org.lower():
            print(f"  Hub: {a['name']} | {a.get('url', '')[:100]}")

c.close()
print("\nDone.")
