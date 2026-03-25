"""Test Fort Worth ArcGIS query syntax."""
import httpx

URL = (
    "https://services5.arcgis.com/3ddLCBXe1bRt7mzj/arcgis/rest/services/"
    "CFW_Open_Data_Certificates_of_Occupancy_Table_view/FeatureServer/0/query"
)

tests = [
    "CODate >= 1735689600000",
    "CODate >= timestamp 1735689600000",
    "CODate >= '2026-01-01'",
    "CODate >= DATE '2026-01-01'",
    "CODate >= date '2026-01-01 00:00:00'",
    "CODate >= TIMESTAMP '2026-01-01 00:00:00'",
]

for w in tests:
    try:
        r = httpx.get(
            URL,
            params={"where": w, "returnCountOnly": "true", "f": "json"},
            follow_redirects=True,
            timeout=15,
        )
        body = r.text[:300]
        print(f"[{r.status_code}] {w!r}")
        if r.status_code == 200 and body.startswith("{"):
            print(f"  -> {body}")
        else:
            print(f"  -> HTML/error")
    except Exception as e:
        print(f"  ERROR: {e}")
