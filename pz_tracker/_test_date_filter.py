"""Verify the date cutoff filter works."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import is_meeting_date_recent

tests = [
    ("Mar 14, 2024", False),
    ("February 17, 2026", True),
    ("Mar 16, 2026", True),
    ("03/03/2026", True),
    ("2026-03-03", True),
    ("2025-12-15", False),
    ("01/15/2026", False),
    ("02/01/2026", True),
    ("unknown", True),
    ("", True),
    ("Jul 28, 2015", False),
    ("October 22, 2024", False),
]

all_pass = True
for date_str, expected in tests:
    result = is_meeting_date_recent(date_str)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  {status}  {date_str!r:30s} -> {result} (expected {expected})")

print(f"\n{'All tests passed!' if all_pass else 'SOME TESTS FAILED!'}")
