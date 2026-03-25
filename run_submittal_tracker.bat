@echo off
REM ─── Submittal Tracker – Scheduled Run ───
REM Runs the submittal tracker for Frisco
REM Logs output to submittal_tracker_run.log

cd /d "C:\Users\divya\Desktop\SparksRadar"

echo ============================================ >> submittal_tracker_run.log
echo Run started: %date% %time% >> submittal_tracker_run.log
echo ============================================ >> submittal_tracker_run.log

"C:\Users\divya\Desktop\SparksRadar\.venv\Scripts\python.exe" -m submittal_tracker.main --city Frisco --sheet-id 14qiDFhK9BIsGDMnRMuVxkpfmfYqNpg5w-6nb48M5WaM --year 2026 >> submittal_tracker_run.log 2>&1

echo Run finished: %date% %time% >> submittal_tracker_run.log
echo. >> submittal_tracker_run.log
