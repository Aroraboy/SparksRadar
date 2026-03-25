"""Research remaining cities - Phase 2: Direct endpoint checks."""
import httpx
import json

def check_endpoint(name, url, where="1=1", count_only=True):
    """Check an ArcGIS endpoint."""
    params = {"where": where, "f": "json"}
    if count_only:
        params["returnCountOnly"] = "true"
    else:
        params["outFields"] = "*"
        params["resultRecordCount"] = "2"
    try:
        r = httpx.get(f"{url}/query", params=params, timeout=15)
        data = r.json()
        if count_only:
            print(f"  [{name}] Count: {data.get('count', 'N/A')}")
        else:
            features = data.get("features", [])
            if features:
                attrs = features[0].get("attributes", {})
                print(f"  [{name}] Fields: {list(attrs.keys())[:15]}")
                # Show a couple values
                for k, v in list(attrs.items())[:8]:
                    print(f"    {k}: {v}")
            else:
                print(f"  [{name}] No features")
        return data
    except Exception as e:
        print(f"  [{name}] Error: {e}")
        return {}

# Check the Building Permits endpoint found in search
# https://services1.arcgis.com/AVP60cs0Q9PEA8rH/arcgis/rest/services/Building_Permits/FeatureServer
print("=== Check mystery Building_Permits endpoint ===")
check_endpoint("AVP60cs", 
    "https://services1.arcgis.com/AVP60cs0Q9PEA8rH/arcgis/rest/services/Building_Permits/FeatureServer/0",
    count_only=False)

# Try Corpus Christi's own GIS server 
print("\n=== CORPUS CHRISTI - Try city GIS server ===")
# Common pattern: services.cctexas.com or gis.cctexas.com
for base in [
    "https://gis.cctexas.com/arcgis/rest/services",
    "https://services.cctexas.com/arcgis/rest/services",
    "https://maps.cctexas.com/arcgis/rest/services",
]:
    try:
        r = httpx.get(f"{base}?f=json", timeout=10)
        print(f"  {base}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            services = data.get("services", [])
            folders = data.get("folders", [])
            print(f"    Folders: {folders[:10]}")
            for svc in services[:5]:
                print(f"    Service: {svc.get('name')} ({svc.get('type')})")
    except Exception as e:
        print(f"  {base}: {e}")

# Corpus Christi Hub search
print("\n=== CORPUS CHRISTI - Hub org search ===")
try:
    r = httpx.get("https://hub.arcgis.com/api/v3/datasets",
        params={"q": "permits", "filter[orgId]": "0J4ZNc4NaTguvRy0"},
        timeout=15)
    data = r.json()
    for item in data.get("data", [])[:10]:
        attrs = item.get("attributes", {})
        name = attrs.get("name", "")
        url = attrs.get("url", "")
        print(f"  {name} | {url}")
except Exception as e:
    print(f"  Error: {e}")

# Grand Prairie - try city GIS
print("\n=== GRAND PRAIRIE - Try city GIS ===")
for base in [
    "https://gis.gptx.org/arcgis/rest/services",
    "https://maps.gptx.org/arcgis/rest/services",
    "https://gis.grandprairietx.org/arcgis/rest/services",
]:
    try:
        r = httpx.get(f"{base}?f=json", timeout=10)
        print(f"  {base}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            folders = data.get("folders", [])
            print(f"    Folders: {folders[:10]}")
    except Exception as e:
        print(f"  {base}: {type(e).__name__}")

# Round Rock - try city GIS
print("\n=== ROUND ROCK - Try city GIS ===")
for base in [
    "https://gis.roundrocktexas.gov/arcgis/rest/services",
    "https://maps.roundrocktexas.gov/arcgis/rest/services",
]:
    try:
        r = httpx.get(f"{base}?f=json", timeout=10)
        print(f"  {base}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            folders = data.get("folders", [])
            print(f"    Folders: {folders[:10]}")
    except Exception as e:
        print(f"  {base}: {type(e).__name__}")

# Carrollton - try city GIS  
print("\n=== CARROLLTON - Try city GIS ===")
for base in [
    "https://gis.cityofcarrollton.com/arcgis/rest/services",
    "https://maps.cityofcarrollton.com/arcgis/rest/services", 
]:
    try:
        r = httpx.get(f"{base}?f=json", timeout=10)
        print(f"  {base}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            folders = data.get("folders", [])
            print(f"    Folders: {folders[:10]}")
    except Exception as e:
        print(f"  {base}: {type(e).__name__}")

# Try Socrata for these cities
print("\n=== SOCRATA DISCOVERY ===")
try:
    r = httpx.get("http://api.us.socrata.com/api/catalog/v1",
        params={"q": "building permits", "domains": "data.corpuschristi.gov,data.gptx.org,data.roundrocktexas.gov,data.cityofcarrollton.com", "limit": 20},
        timeout=15)
    data = r.json()
    for result in data.get("results", []):
        res = result.get("resource", {})
        name = res.get("name", "")
        domain = result.get("metadata", {}).get("domain", "")
        uid = res.get("id", "")
        print(f"  [{domain}] {name} | {uid}")
    if not data.get("results"):
        print("  No results")
except Exception as e:
    print(f"  Error: {e}")

# Try broader Socrata search for each city
print("\n=== SOCRATA - Individual city searches ===")
for city in ["corpus christi", "grand prairie texas", "round rock texas", "carrollton texas"]:
    try:
        r = httpx.get("http://api.us.socrata.com/api/catalog/v1",
            params={"q": f"building permits {city}", "limit": 5},
            timeout=15)
        data = r.json()
        results = data.get("results", [])
        print(f"\n  [{city}] Found {len(results)} results:")
        for result in results[:3]:
            res = result.get("resource", {})
            name = res.get("name", "")
            domain = result.get("metadata", {}).get("domain", "")
            uid = res.get("id", "")
            print(f"    [{domain}] {name} | {uid}")
    except Exception as e:
        print(f"  [{city}] Error: {e}")

print("\nDone!")
