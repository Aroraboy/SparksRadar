"""Find past P&Z events via CivicClerk API with date filter."""

import asyncio
import httpx
import json
from datetime import datetime, timezone


async def main():
    bases = {
        "Sherman": "https://SHERMANTX.api.civicclerk.com/v1",
        "Elgin": "https://elgintx.api.civicclerk.com/v1",
    }
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
        for city, base in bases.items():
            print(f"\n{'='*60}\n  {city}\n{'='*60}")

            # Get past events, newest first
            resp = await client.get(
                f"{base}/Events",
                params={
                    "$top": "30",
                    "$orderby": "eventDate desc",
                    "$filter": f"eventDate lt {now_iso}",
                }
            )
            data = resp.json()
            events = data.get("value", [])

            pz_events = [
                e for e in events
                if any(kw in (e.get("eventName", "") + e.get("categoryName", "")).lower()
                       for kw in ["planning", "zoning", "p&z"])
            ]

            print(f"  Past events: {len(events)}, P&Z: {len(pz_events)}")
            for e in pz_events[:5]:
                aid = e.get("agendaId", 0)
                print(f"    id={e['id']}  date={e['eventDate'][:10]}  agendaId={aid}  name={e['eventName'][:60]}")

            # Pick first with agendaId > 0
            with_agenda = [e for e in pz_events if (e.get("agendaId") or 0) > 0]
            if with_agenda:
                latest = with_agenda[0]
                aid = latest["agendaId"]
                print(f"\n  Best match: id={latest['id']} date={latest['eventDate'][:10]} agendaId={aid}")

                # Try download
                dl_url = f"{base}/Meetings/GetMeetingFileStream(fileId={aid},plainText=false)"
                dresp = await client.get(dl_url)
                ct = dresp.headers.get("content-type", "")
                print(f"  Download: status={dresp.status_code} CT={ct} size={len(dresp.content)} isPDF={dresp.content[:4] == b'%PDF'}")

                # Also check meeting items
                mresp = await client.get(f"{base}/Meetings/{aid}")
                mdata = mresp.json()
                items = mdata.get("items", [])
                pfiles = mdata.get("publishedFiles", [])
                print(f"  Meeting info: items={len(items)}, publishedFiles={len(pfiles)}")
                print(f"  agendaIsPublish={mdata.get('agendaIsPublish')}, agendaPacketIsPublish={mdata.get('agendaPacketIsPublish')}")

                if pfiles:
                    for pf in pfiles[:3]:
                        print(f"    File: {json.dumps(pf)[:200]}")
                if items:
                    for item in items[:3]:
                        print(f"    Item: {json.dumps(item)[:200]}")

asyncio.run(main())
