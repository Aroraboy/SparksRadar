import requests
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== ROUND ROCK - Building Permits Layer 44 =====
print("=" * 60)
print("ROUND ROCK - Building Permits Layer 44")
print("=" * 60)

base = "https://cityworks.roundrocktexas.gov/Cityworks_prod/gis/1/1/rest/services/qe/FeatureServer/44"

# Get layer info
try:
    r = requests.get(base, params={"f": "json"}, timeout=30, verify=False)
    data = r.json()
    print("Name:", data.get("name"))
    print("Description:", data.get("description"))
    print("Type:", data.get("type"))
    fields = data.get("fields", [])
    print(f"Fields ({len(fields)}):")
    for f in fields:
        print(f"  {f['name']} ({f['type']})")
except Exception as e:
    print(f"Layer info error: {e}")

# Get record count
print()
try:
    r = requests.get(base + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, timeout=30, verify=False)
    data = r.json()
    print("Total record count:", data.get("count"))
except Exception as e:
    print(f"Count error: {e}")

# Get sample records
print()
try:
    r = requests.get(base + "/query", params={
        "where": "1=1",
        "outFields": "*",
        "resultRecordCount": "3",
        "f": "json"
    }, timeout=30, verify=False)
    data = r.json()
    features = data.get("features", [])
    print(f"Sample records ({len(features)}):")
    for feat in features[:2]:
        attrs = feat.get("attributes", {})
        for k, v in list(attrs.items()):
            print(f"  {k}: {v}")
        print("---")
except Exception as e:
    print(f"Sample error: {e}")

# Check 2026 data
print()
print("=== 2026 DATA CHECK ===")
try:
    r = requests.get(base + "/query", params={
        "where": "DateCreated >= DATE '2026-01-01'",
        "returnCountOnly": "true",
        "f": "json"
    }, timeout=30, verify=False)
    data = r.json()
    print("Records from 2026:", data.get("count"))
    if data.get("error"):
        print("Error:", data["error"])
except Exception as e:
    print(f"2026 check error: {e}")

# ===== Also check Layer 19 (Building Permits - Issued) =====
print()
print("=" * 60)
print("ROUND ROCK - Building Permits Issued (Layer 19)")
print("=" * 60)

base19 = "https://cityworks.roundrocktexas.gov/Cityworks_prod/gis/1/1/rest/services/qe/FeatureServer/19"
try:
    r = requests.get(base19, params={"f": "json"}, timeout=30, verify=False)
    data = r.json()
    print("Name:", data.get("name"))
    fields = data.get("fields", [])
    print(f"Fields ({len(fields)}):")
    for f in fields:
        print(f"  {f['name']} ({f['type']})")
except Exception as e:
    print(f"Layer 19 info error: {e}")

try:
    r = requests.get(base19 + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"}, timeout=30, verify=False)
    data = r.json()
    print("Total record count:", data.get("count"))
except Exception as e:
    print(f"Count error: {e}")

# ===== Check hosted Feature Service for Round Rock =====
print()
print("=" * 60)
print("ROUND ROCK - Hosted ArcGIS Feature Service")
print("=" * 60)

hosted_base = "https://services.arcgis.com/KaARkuoKF9vrGr3P/arcgis/rest/services"
try:
    r = requests.get(hosted_base, params={"f": "json"}, timeout=30)
    data = r.json()
    services = data.get("services", [])
    print(f"Available services ({len(services)}):")
    for svc in services:
        print(f"  {svc['name']} ({svc['type']})")
except Exception as e:
    print(f"Services list error: {e}")

# ===== CORPUS CHRISTI =====
print()
print("=" * 60)
print("CORPUS CHRISTI - Checking for open data")
print("=" * 60)

# Try ArcGIS REST services for CC
cc_urls = [
    "https://services.arcgis.com/0L95CJ0VTaxqcmED/arcgis/rest/services",  # CC org
    "https://gis.cctexas.com/arcgis/rest/services",
    "https://maps.cctexas.com/arcgis/rest/services",
]
for url in cc_urls:
    try:
        r = requests.get(url, params={"f": "json"}, timeout=15)
        data = r.json()
        services = data.get("services", [])
        folders = data.get("folders", [])
        if services or folders:
            print(f"\n{url}")
            if folders:
                print(f"  Folders: {folders}")
            for svc in services[:10]:
                print(f"  {svc['name']} ({svc['type']})")
            if len(services) > 10:
                print(f"  ... and {len(services)-10} more")
    except Exception as e:
        print(f"  {url}: {e}")

# ===== GRAND PRAIRIE =====
print()
print("=" * 60)
print("GRAND PRAIRIE - Checking for open data")
print("=" * 60)

gp_urls = [
    "https://gis.gptx.org/arcgis/rest/services",
    "https://maps.gptx.org/arcgis/rest/services",
    "https://services.arcgis.com/JKvhDEkvHlAiQYrB/arcgis/rest/services",  # GP org guess
]
for url in gp_urls:
    try:
        r = requests.get(url, params={"f": "json"}, timeout=15)
        data = r.json()
        services = data.get("services", [])
        folders = data.get("folders", [])
        if services or folders:
            print(f"\n{url}")
            if folders:
                print(f"  Folders: {folders}")
            for svc in services[:10]:
                print(f"  {svc['name']} ({svc['type']})")
            if len(services) > 10:
                print(f"  ... and {len(services)-10} more")
    except Exception as e:
        print(f"  {url}: {e}")

# ===== CARROLLTON =====
print()
print("=" * 60)
print("CARROLLTON - Checking for open data")
print("=" * 60)

carr_urls = [
    "https://services.arcgis.com/o731hPfw3YndegMz/arcgis/rest/services",
    "https://gis.cityofcarrollton.com/arcgis/rest/services",
]
for url in carr_urls:
    try:
        r = requests.get(url, params={"f": "json"}, timeout=15)
        data = r.json()
        services = data.get("services", [])
        folders = data.get("folders", [])
        if services or folders:
            print(f"\n{url}")
            if folders:
                print(f"  Folders: {folders}")
            for svc in services[:10]:
                print(f"  {svc['name']} ({svc['type']})")
            if len(services) > 10:
                print(f"  ... and {len(services)-10} more")
    except Exception as e:
        print(f"  {url}: {e}")
