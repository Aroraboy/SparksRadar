"""Migrate Google Sheets from per-city tabs to per-portal-type tabs."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from writers.google_sheets_writer import _get_client, SPREADSHEET_ID, _PORTAL_TAB_NAMES
from config import EXCEL_COLUMNS, DEFAULT_CITIES

client = _get_client()
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# Step 1: Read all data from existing city tabs
city_data = {}
for ws in spreadsheet.worksheets():
    if ws.title in ("Sheet1",):
        continue
    rows = ws.get_all_values()
    if len(rows) > 1:  # has data beyond header
        city_data[ws.title] = rows[1:]  # skip header
        print(f"  Read {len(rows)-1} row(s) from '{ws.title}'")

# Step 2: Group by portal type
portal_rows = {}
for city_name, rows in city_data.items():
    city_info = DEFAULT_CITIES.get(city_name, {})
    portal_type = city_info.get("portal_type", "")
    tab_name = _PORTAL_TAB_NAMES.get(portal_type, portal_type or city_name)
    portal_rows.setdefault(tab_name, []).extend(rows)

print("\nGrouped data:")
for tab, rows in portal_rows.items():
    print(f"  {tab}: {len(rows)} row(s)")

# Step 3: Delete old city tabs
for ws in spreadsheet.worksheets():
    if ws.title not in ("Sheet1",):
        print(f"  Deleting old tab: '{ws.title}'")
        spreadsheet.del_worksheet(ws)

# Step 4: Create portal-type tabs and write data
for tab_name, rows in portal_rows.items():
    ws = spreadsheet.add_worksheet(title=tab_name, rows=max(100, len(rows) + 5), cols=len(EXCEL_COLUMNS))
    ws.append_row(EXCEL_COLUMNS, value_input_option="RAW")
    if rows:
        ws.append_rows(rows, value_input_option="RAW")
    print(f"  Created '{tab_name}' with {len(rows)} row(s)")

print("\nMigration complete!")

# Show final state
print("\nFinal tabs:")
for ws in spreadsheet.worksheets():
    all_vals = ws.get_all_values()
    data_rows = len(all_vals) - 1 if len(all_vals) > 0 else 0
    print(f"  '{ws.title}' - {data_rows} data row(s)")
