@echo off
rem RASAD - rebuild the demo data from scratch (same seed = same demo every time).
rem Clears all approvals and the audit log. Works offline.
cd /d "%~dp0"

curl -s -o nul -m 2 http://127.0.0.1:8000/api/health && (
  echo RASAD is still running. Close the RASAD window first, then run reset_demo.bat again.
  pause
  exit /b 1
)

echo Rebuilding the demo data (under a minute) ...
.venv\Scripts\python -m backend.gen_data || (echo Something went wrong. See docs\TROUBLESHOOTING.md & pause & exit /b 1)
echo.
echo Demo data is fresh. Now double-click start.bat.
pause
