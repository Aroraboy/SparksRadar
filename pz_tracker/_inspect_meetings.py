"""Check meeting details and file availability for past P&Z meetings."""

import asyncio
import httpx
import json
from datetime import datetime, timezone


async def main():
    bases = {
        "Sherman": "https://SHERMANTX.api.civicclerk.com/v1",
        "Elgin": "https://elgintx.api.civicclerk.com/v1",
    }

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for city, base in bases.items():
            print(f"\n{'='*60}\n  {city}\n{'='*60}")

            # Get recent P&Z events
            # Try broader filter first
            resp = await client.get(
                f"{base}/Events",
                params={"$top": "20", "$orderby": "eventDate desc"}
            )
            events = resp.json().get("value", [])

            pz_events = [
                e for e in events
                if any(kw in (e.get("eventName", "") + e.get("categoryName", "")).lower()
                       for kw in ["planning", "zoning", "p&z"])
            ]

            now = datetime.now(timezone.utc)
            print(f"\n  P&Z Events (from {len(events)} total):")
            for e in pz_events[:5]:
                edate = e["eventDate"]
                aid = e.get("agendaId", 0)
                is_past = datetime.fromisoformat(edate.replace("Z", "+00:00")) < now
                print(f"    id={e['id']}  date={edate[:10]}  agendaId={aid}  past={is_past}  name={e['eventName'][:60]}")

            # Find most recent past event with an agendaId
            past_pz = [
                e for e in pz_events
                if (e.get("agendaId") or 0) > 0
                and datetime.fromisoformat(e["eventDate"].replace("Z", "+00:00")) < now
            ]

            if past_pz:
                latest = past_pz[0]
                aid = latest["agendaId"]
                print(f"\n  Most recent past P&Z with agenda: id={latest['id']} date={latest['eventDate'][:10]} agendaId={aid}")

                # Check meeting details
                mresp = await client.get(f"{base}/Meetings/{aid}")
                mdata = mresp.json()
                print(f"  Meeting {aid}:")
                print(f"    agendaIsPublish: {mdata.get('agendaIsPublish')}")
                print(f"    agendaPacketIsPublish: {mdata.get('agendaPacketIsPublish')}")
                print(f"    publishedFiles: {mdata.get('publishedFiles', [])}")
                print(f"    items count: {len(mdata.get('items', []))}")

                # Try downloading the meeting file
                dl_url = f"{base}/Meetings/GetMeetingFileStream(fileId={aid},plainText=false)"
                print(f"  Downloading: {dl_url}")
                dresp = await client.get(dl_url)
                ct = dresp.headers.get("content-type", "")
                print(f"    Status: {dresp.status_code}  CT: {ct}  Size: {len(dresp.content)} bytes")
                if dresp.content[:4] == b"%PDF":
                    print(f"    ✓ Valid PDF!")
                else:
                    print(f"    First bytes: {dresp.content[:30]}")

                # Also check published files - iterate
                if mdata.get("items"):
                    for item in mdata["items"][:3]:
                        print(f"    Item: {json.dumps(item)[:200]}")
            else:
                print("  No past P&Z events with agendaId found!")

asyncio.run(main())
