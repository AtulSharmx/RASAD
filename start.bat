@echo off
rem RASAD - one-click start. The very first run on a new laptop needs internet once (to install
rem Python and web packages); after that everything works offline.
cd /d "%~dp0"
title RASAD

rem Already running? Then just open the browser instead of starting a second copy.
curl -s -o nul -m 2 http://127.0.0.1:8000/api/health && (
  echo RASAD is already running. Opening it in the browser ...
  start http://localhost:8000
  goto :eof
)

if not exist .venv\Scripts\python.exe (
  echo [1/4] First run: setting up Python ^(needs internet once^) ...
  py -3 -m venv .venv || goto :fail
  .venv\Scripts\python -m pip install -q -r requirements.txt || goto :fail
)

rem Windows Smart App Control checks each new library file once; the first try can be blocked.
for /l %%i in (1,1,3) do (
  .venv\Scripts\python -c "import pandas, lightgbm, ortools.sat.python.cp_model, fastapi" 2>nul && goto :pyok
  echo     Windows is checking the new files, trying again ...
)
goto :fail
:pyok

if not exist frontend\dist\index.html (
  echo [2/4] Building the screens ...
  pushd frontend
  if not exist node_modules (
    echo     First run: installing web packages ^(needs internet once^) ...
    call npm install --silent || goto :fail
  )
  call npm run build || goto :fail
  popd
)

if not exist data\rasad.db (
  echo [3/4] Creating demo data ^(under a minute^) ...
  .venv\Scripts\python -m backend.gen_data || goto :fail
)

echo [4/4] RASAD is running at http://localhost:8000
echo       Keep this window open during the demo. Close it to stop RASAD.
echo       The first screens can take about 40 seconds while results are prepared.
start "" cmd /c "timeout /t 4 >nul & start http://localhost:8000"
.venv\Scripts\python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
goto :eof

:fail
echo.
echo Something went wrong. Take a photo of this window and see docs\TROUBLESHOOTING.md
pause
