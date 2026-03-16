"""Run the pipeline for new cities only (skip already-processed ones)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from config import DEFAULT_CITIES
from main import run_pipeline

ALREADY_DONE = {"Lago Vista", "Manor", "Sherman", "Victoria", "Elgin"}

new_cities = {k: v for k, v in DEFAULT_CITIES.items() if k not in ALREADY_DONE}
print(f"Running pipeline for {len(new_cities)} new cities:")
for c in new_cities:
    print(f"  - {c} ({new_cities[c]['portal_type']})")
print()

summary = run_pipeline(new_cities)

print("\n" + "=" * 60)
print("RESULTS:")
print("=" * 60)
total = 0
for city, count in summary.items():
    print(f"  {city}: {count} record(s)")
    total += count
print(f"\nTotal: {total} new records across {len(summary)} cities")
