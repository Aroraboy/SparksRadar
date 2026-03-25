"""Research remaining cities for permit data APIs."""
import httpx
import json

def search_arcgis_org(org_url, query="building permits"):
    """Search an ArcGIS organization for datasets."""
    url = f"{org_url}/sharing/rest/search"
    params = {"q": query, "f": "json", "num": 20}
    try:
        r = httpx.get(url, params=params, timeout=15)
        data = r.json()
        results = data.get("results", [])
        for item in results:
            title = item.get("title", "")
            itype = item.get("type", "")
            iurl = item.get("url", "")
            print(f"  {title} | {itype} | {iurl}")
        return results
    except Exception as e:
        print(f"  Error: {e}")
        return []

def search_socrata(domain, query="permits"):
    """Search Socrata domain for datasets."""
    url = f"https://{domain}/api/views/metadata/v1"
    try:
        r = httpx.get(url, params={"limit": 20}, timeout=15)
        data = r.json()
        for item in data:
            name = item.get("name", "")
            if any(kw in name.lower() for kw in ["permit", "building", "construction", "certificate"]):
                uid = item.get("id", "")
                print(f"  {name} | {uid}")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return []

def try_arcgis_rest(base_url):
    """Try to query an ArcGIS REST endpoint."""
    url = f"{base_url}/query"
    params = {"where": "1=1", "returnCountOnly": "true", "f": "json"}
    try:
        r = httpx.get(url, params=params, timeout=15)
        data = r.json()
        count = data.get("count", "N/A")
        print(f"  Count: {count}")
        # Get sample
        params2 = {"where": "1=1", "outFields": "*", "resultRecordCount": "1", "f": "json"}
        r2 = httpx.get(url, params=params2, timeout=15)
        d2 = r2.json()
        features = d2.get("features", [])
        if features:
            attrs = features[0].get("attributes", {})
            print(f"  Fields: {list(attrs.keys())}")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return {}

# ============ CORPUS CHRISTI ============
print("\n=== CORPUS CHRISTI ===")
print("\n-- ArcGIS Org Search (permits) --")
search_arcgis_org("https://corpus.maps.arcgis.com", "permits")

print("\n-- ArcGIS Org Search (building) --")
search_arcgis_org("https://corpus.maps.arcgis.com", "building")

# ============ GRAND PRAIRIE ============
print("\n=== GRAND PRAIRIE ===")
print("\n-- ArcGIS Hub search --")
try:
    r = httpx.get("https://hub.arcgis.com/api/v3/datasets", 
                   params={"q": "permits grand prairie texas", "filter[type]": "Feature Service"},
                   timeout=15)
    data = r.json()
    for item in data.get("data", [])[:10]:
        attrs = item.get("attributes", {})
        name = attrs.get("name", "")
        url = attrs.get("url", "")
        org = attrs.get("organization", "")
        if "grand prairie" in name.lower() or "grand prairie" in org.lower():
            print(f"  {name} | {org} | {url}")
except Exception as e:
    print(f"  Error: {e}")

print("\n-- Try Grand Prairie ArcGIS org --")
search_arcgis_org("https://grandprairietx.maps.arcgis.com", "permits")

# ============ ROUND ROCK ============
print("\n=== ROUND ROCK ===")
print("\n-- ArcGIS org search --")
search_arcgis_org("https://roundrocktexas.maps.arcgis.com", "permits")

print("\n-- Socrata search --")
# Round Rock might use data.roundrocktexas.gov or similar
try:
    r = httpx.get("https://data.roundrocktexas.gov/api/views/metadata/v1", 
                   params={"limit": 20}, timeout=15)
    if r.status_code == 200:
        for item in r.json():
            name = item.get("name", "")
            uid = item.get("id", "")
            print(f"  {name} | {uid}")
    else:
        print(f"  HTTP {r.status_code}")
except Exception as e:
    print(f"  No Socrata: {e}")

# ============ CARROLLTON ============
print("\n=== CARROLLTON ===")
print("\n-- ArcGIS org search --")
search_arcgis_org("https://carrolltontx.maps.arcgis.com", "permits")

print("\n-- Try cityofcarrollton --")
search_arcgis_org("https://cityofcarrollton.maps.arcgis.com", "permits")

print("\nDone!")
