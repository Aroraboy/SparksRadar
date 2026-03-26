"""Check CC permit report sub-pages and Dallas sdc_public."""
import httpx
import re

c = httpx.Client(follow_redirects=True, timeout=15, headers={"User-Agent": "Mozilla/5.0"})

# CC - Monthly permit history reports
print("=== CC MONTHLY PERMIT HISTORY ===")
r = c.get("https://www.corpuschristitx.gov/department-directory/development-services/reports/monthly-permit-history-reports/")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    links = re.findall(r'href="([^"]*)"', r.text, re.I)
    dl = [l for l in links if any(ext in l.lower() for ext in [".pdf", ".xlsx", ".xls", ".csv"])]
    print(f"Download links: {len(dl)}")
    for d in dl[:20]:
        print(f"  {d}")
    # Look for 2026/2025 references
    refs = [l for l in links if "2026" in l or "2025" in l]
    print(f"2025/2026 links: {len(refs)}")
    for r2 in refs[:10]:
        print(f"  {r2}")

# CC - Fiscal permit reports
print("\n=== CC FISCAL PERMIT REPORTS ===")
r = c.get("https://www.corpuschristitx.gov/department-directory/development-services/reports/fiscal-permit-history-reports-by-month/")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    dl = re.findall(r'href="([^"]*\.(?:pdf|xlsx|xls|csv))"', r.text, re.I)
    print(f"Download links: {len(dl)}")
    for d in dl[:20]:
        print(f"  {d}")
    # Extract text around 'permit' or 'report' or '2026'
    text = re.sub(r"<[^>]+>", " ", r.text)
    text = re.sub(r"\s+", " ", text)
    for kw in ["2026", "January", "February", "March"]:
        idx = text.find(kw)
        if idx >= 0:
            print(f"  Near '{kw}': ...{text[max(0,idx-60):idx+80]}...")

# CC - CO monthly reports
print("\n=== CC CO MONTHLY REPORTS ===")
r = c.get("https://www.corpuschristitx.gov/department-directory/development-services/reports/certificate-of-occupancy-monthly-reports/")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    dl = re.findall(r'href="([^"]*\.(?:pdf|xlsx|xls|csv))"', r.text, re.I)
    print(f"Download links: {len(dl)}")
    for d in dl[:20]:
        print(f"  {d}")

# Dallas sdc_public folder
print("\n=== DALLAS sdc_public ===")
r = c.get("https://gis.dallascityhall.com/arcgis/rest/services/sdc_public", params={"f": "json"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    for svc in data.get("services", []):
        print(f"  {svc['name']} | {svc['type']}")

# Check all Dallas GIS folders for permit-related services
print("\n=== DALLAS ALL FOLDERS ===")
for folder in ["Basemap", "Bond", "Crm_public", "Pbw_public", "sdc_public", "ToolServices", "Utilities"]:
    try:
        r = c.get(f"https://gis.dallascityhall.com/arcgis/rest/services/{folder}", params={"f": "json"})
        if r.status_code == 200:
            svcs = r.json().get("services", [])
            for svc in svcs:
                n = svc["name"].lower()
                if any(k in n for k in ["permit", "build", "develop", "construct", "inspect"]):
                    print(f"  [{folder}] {svc['name']} | {svc['type']}")
    except:
        pass

c.close()
print("\nDone.")
