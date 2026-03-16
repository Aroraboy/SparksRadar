"""List existing Google Sheets tabs and migrate to portal-type grouping."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from writers.google_sheets_writer import _get_client, SPREADSHEET_ID

client = _get_client()
spreadsheet = client.open_by_key(SPREADSHEET_ID)

print("Existing tabs:")
for ws in spreadsheet.worksheets():
    rows = ws.row_count
    print(f"  '{ws.title}' - {rows} rows")
