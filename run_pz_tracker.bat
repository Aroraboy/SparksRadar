@echo off
REM ─── P&Z Tracker – Scheduled Run ───
REM Runs the full P&Z pipeline for all cities
REM Logs output to pz_tracker_run.log

cd /d "C:\Users\divya\Desktop\SparksRadar"

echo ============================================ >> pz_tracker_run.log
echo Run started: %date% %time% >> pz_tracker_run.log
echo ============================================ >> pz_tracker_run.log

"C:\Users\divya\Desktop\SparksRadar\.venv\Scripts\python.exe" -m pz_tracker.main >> pz_tracker_run.log 2>&1

echo Run finished: %date% %time% >> pz_tracker_run.log
echo. >> pz_tracker_run.log
