"""Quick test of CivicClerk API for failing cities."""
import httpx
import asyncio


async def test(subdomain, city):
    base = f"https://{subdomain}.api.civicclerk.com/v1"
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{base}/Events")
        print(f"{city:13s} Events(raw)   -> {r.status_code}  {r.text[:200]}")
        r2 = await c.get(f"{base}/Settings/GetIdentityServerConfiguration")
        print(f"{city:13s} Settings      -> {r2.status_code}  {r2.text[:150]}")
        print()


async def main():
    # 500-error cities
    for sub, city in [
        ("sachsetx", "Sachse"),
        ("alvaradotx", "Alvarado"),
        ("kaufmantx", "Kaufman"),
    ]:
        await test(sub, city)


asyncio.run(main())
