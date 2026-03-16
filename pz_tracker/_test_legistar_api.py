"""Quick test of the Legistar web API to understand its structure."""
import httpx
import json

client = httpx.Client(timeout=30)

# Try different client names matching the legistar subdomains
clients = ["mckinney", "plano", "coppell", "cityofkeller", "keller",
           "mansfield", "garland", "gptx", "rockwall",
           "richardson", "leander", "littleelm", "denton", "arlington",
           "carrollton", "pflugerville", "grapevine"]

working = {}
for name in clients:
    try:
        resp = client.get(f"https://webapi.legistar.com/v1/{name}/Bodies")
        if resp.status_code == 200:
            data = resp.json()
            pz_bodies = [b for b in data if any(kw in b["BodyName"].lower()
                         for kw in ["zon", "plan", "p&z", "p & z"])]
            if pz_bodies:
                print(f"\n{name}: P&Z bodies found:")
                for b in pz_bodies:
                    print(f"  ID={b['BodyId']}  Name={b['BodyName']}")
                working[name] = pz_bodies[0]["BodyId"]
            else:
                print(f"{name}: {len(data)} bodies but no P&Z match")
        else:
            print(f"{name}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"{name}: ERROR {type(e).__name__}")

# Now test getting Events for the first working client
if working:
    client_name = list(working.keys())[0]
    body_id = working[client_name]
    print(f"\n\n=== Testing Events for {client_name}, BodyId={body_id} ===")

    resp = client.get(
        f"https://webapi.legistar.com/v1/{client_name}/Events",
        params={"$filter": f"EventBodyId eq {body_id}", "$orderby": "EventDate desc", "$top": "5"}
    )
    events = resp.json()
    for e in events:
        print(f"\nEvent ID={e['EventId']}  Date={e['EventDate']}  Body={e.get('EventBodyName')}")
        print(f"  AgendaFile={e.get('EventAgendaFile')}")
        print(f"  MinutesFile={e.get('EventMinutesFile')}")
        print(f"  AgendaLastPublished={e.get('EventAgendaLastPublishedUTC')}")
        # Check for agenda items with attachments
        items_resp = client.get(
            f"https://webapi.legistar.com/v1/{client_name}/Events/{e['EventId']}/EventItems",
            params={"Attachments": "1"}
        )
        items = items_resp.json()
        pz_items = [i for i in items if any(kw in (i.get("EventItemTitle") or "").lower()
                    for kw in ["rezon", "plat", "site plan", "subdivision", "zoning"])]
        if pz_items:
            print(f"  {len(pz_items)} P&Z-relevant items:")
            for it in pz_items[:3]:
                print(f"    - {it.get('EventItemTitle', '')[:120]}")
                for att in (it.get("EventItemMatterAttachments") or []):
                    print(f"      Attachment: {att.get('MatterAttachmentName')} -> {att.get('MatterAttachmentHyperlink')}")
        break  # just test the first event
