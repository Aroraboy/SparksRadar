"""Research cities - Socrata and web portal searches."""
import httpx
import json

# Try Socrata catalog with HTTPS
print("=== SOCRATA CATALOG ===")
for city in ["corpus christi", "grand prairie", "round rock", "carrollton"]:
    try:
        r = httpx.get("https://api.us.socrata.com/api/catalog/v1",
            params={"q": f"building permits {city} texas", "limit": 5},
            timeout=15, follow_redirects=True)
        print(f"\n[{city}] HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            for result in data.get("results", [])[:3]:
                res = result.get("resource", {})
                dom = result.get("metadata", {}).get("domain", "")
                name = res.get("name", "")
                uid = res.get("id", "")
                print(f"  [{dom}] {name} | {uid}")
    except Exception as e:
        print(f"[{city}] Error: {e}")

# Try direct open data domains
print("\n\n=== DIRECT OPEN DATA PORTALS ===")
domains_to_try = [
    ("Corpus Christi", "data.cctexas.com"),
    ("Corpus Christi", "cctexas-admin.data.socrata.com"),
    ("Grand Prairie", "data.gptx.org"),
    ("Grand Prairie", "data.grandprairietx.org"),
    ("Round Rock", "data.roundrocktexas.gov"),
    ("Carrollton", "data.cityofcarrollton.com"),
]

for city, domain in domains_to_try:
    try:
        r = httpx.get(f"https://{domain}", timeout=10, follow_redirects=True)
        print(f"  [{city}] {domain}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  [{city}] {domain}: {type(e).__name__}")

# Try ArcGIS Hub search more specifically
print("\n\n=== ARCGIS HUB - Targeted org searches ===")
# Search for each city's org on ArcGIS
for city, org_patterns in [
    ("Corpus Christi", ["corpus christi", "cctexas"]),
    ("Grand Prairie", ["grand prairie", "gptx"]),
    ("Round Rock", ["round rock"]),
    ("Carrollton", ["carrollton"]),
]:
    for pat in org_patterns:
        try:
            r = httpx.get("https://hub.arcgis.com/api/v3/datasets",
                params={"q": f"permits {pat}", "page[size]": 5},
                timeout=15)
            data = r.json()
            found = False
            for item in data.get("data", []):
                attrs = item.get("attributes", {})
                org = attrs.get("organization", "").lower()
                name = attrs.get("name", "")
                url = attrs.get("url", "")
                if pat.replace(" ", "") in org.replace(" ", "") or pat in org:
                    found = True
                    print(f"  [{city}] {name} | org={attrs.get('organization','')} | {url}")
            if not found:
                # Check if any of the results mention the city
                for item in data.get("data", []):
                    attrs = item.get("attributes", {})
                    name = attrs.get("name", "").lower()
                    if pat.split()[0] in name:
                        print(f"  [{city}] {attrs.get('name','')} | org={attrs.get('organization','')} | {attrs.get('url','')}")
        except Exception as e:
            print(f"  [{city}] Error searching '{pat}': {e}")

# Check if Grand Prairie has an ArcGIS org
print("\n\n=== GRAND PRAIRIE - ArcGIS REST ===")
# Grand Prairie often uses gptx.org
gp_urls = [
    "https://gis.gptx.org/server/rest/services",
    "https://maps.gptx.org/server/rest/services",
    "https://gis.gptx.org/portal/sharing/rest/search",
]
for url in gp_urls:
    try:
        params = {"f": "json"} if "search" not in url else {"q": "permits", "f": "json", "num": 5}
        r = httpx.get(url, params=params, timeout=10)
        print(f"  {url}: HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if "services" in data:
                for svc in data["services"][:5]:
                    print(f"    {svc.get('name')} | {svc.get('type')}")
            if "folders" in data:
                print(f"    Folders: {data['folders'][:10]}")
            if "results" in data:
                for res in data["results"][:5]:
                    print(f"    {res.get('title')} | {res.get('type')}")
    except Exception as e:
        print(f"  {url}: {type(e).__name__}")

print("\nDone!")
