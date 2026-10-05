@echo off
rem RASAD - rebuild the demo data from scratch (same seed = same demo every time).
cd /d "%~dp0"
.venv\Scripts\python -m backend.gen_data || (echo Something went wrong. Send a photo of this window to Claude. & pause & exit /b 1)
echo Demo data is fresh. Now run start.bat.
pause
