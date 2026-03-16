"""Try various CivicClerk API endpoints to find agenda file download."""

import asyncio
import httpx
import json

SHERMAN_BASE = "https://SHERMANTX.api.civicclerk.com/v1"
# Event 1354 has agendaId 1244

URLS = [
    f"{SHERMAN_BASE}/Meetings/1244",
    f"{SHERMAN_BASE}/Agendas(1244)",
    f"{SHERMAN_BASE}/Agendas/1244",
    f"{SHERMAN_BASE}/Events(1354)/EventFiles",
    f"{SHERMAN_BASE}/Events(1354)/Agenda",
    f"{SHERMAN_BASE}/Meetings/GetMeetingFileStream(fileId=1244,plainText=false)",
    # Try to query events for P&Z with files
    f"{SHERMAN_BASE}/Events?$filter=categoryName eq 'Planning and Zoning Commission'&$top=3&$orderby=eventDate desc",
    # Try expanding files
    f"{SHERMAN_BASE}/Events?$filter=id eq 1354&$expand=EventFiles",
    # Try OData
    f"{SHERMAN_BASE}/Events?$top=1&$filter=id eq 1277",
]


async def main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for url in URLS:
            print(f"\n--- {url.split('v1/')[1] if 'v1/' in url else url} ---")
            try:
                resp = await client.get(url)
                ct = resp.headers.get("content-type", "")
                if "json" in ct or "odata" in ct:
                    try:
                        data = resp.json()
                        print(json.dumps(data, indent=2)[:1000])
                    except:
                        print(resp.text[:500])
                elif "pdf" in ct:
                    print(f"  PDF! {len(resp.content)} bytes")
                else:
                    print(f"  Status={resp.status_code} CT={ct}")
                    print(f"  Body: {resp.text[:300]}")
            except Exception as e:
                print(f"  ERROR: {e}")

asyncio.run(main())
