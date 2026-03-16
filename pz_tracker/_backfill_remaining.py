"""Backfill no-data entries for remaining cities that haven't been written to Excel/Sheets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

from config import DEFAULT_CITIES
from writers.excel_writer import write_no_data_record
from writers.google_sheets_writer import write_no_data_to_sheets

# Cities that need no-data entries with reasons
NO_DATA_CITIES = {
    "McKinney": "No relevant data found – Groq API daily limit reached during processing",
    "Denton": "No relevant data found – Legistar API error",
    "Coppell": "No relevant data found – Legistar API error",
    "Mansfield": "No relevant data found – Legistar API error",
    "Garland": "No relevant data found – Legistar API error",
    "Arlington": "No relevant data found – Legistar API error",
    "Rockwall": "No relevant data found – Legistar API error",
    "Richardson": "No relevant data found – Legistar API error",
    "Grand Prairie": "No relevant data found – Legistar API error",
    "Murphy": "No relevant data found – no P&Z agenda found on CivicWeb portal",
}

for city, reason in NO_DATA_CITIES.items():
    info = DEFAULT_CITIES.get(city, {})
    portal_type = info.get("portal_type", "")
    try:
        write_no_data_record(city, reason=reason)
        print(f"  Excel: {city}")
    except Exception as e:
        print(f"  Excel ERROR {city}: {e}")
    try:
        write_no_data_to_sheets(city, portal_type=portal_type, reason=reason)
        print(f"  Sheets: {city}")
    except Exception as e:
        print(f"  Sheets ERROR {city}: {e}")

print("\nDone!")
