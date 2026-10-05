# PROGRESS — RASAD

Read `BUILD_PROMPT.md` (the brief), `docs/PLAN.md` (the agreed plan, including the changes agreed on 5 Oct) and this file before continuing.

## Done
- **Step 0 (5 Oct 2026):** research in `docs/FACTS.md`, plan in `docs/PLAN.md`. Plan approved with changes: drone payload 15/20 kg, the Joint Primer added, the IoT fuel-sensor feed is part of the base, GitHub backup.
- **Step 2 (in progress, 5 Oct):**
  - Python 3.14 venv (`.venv`) with fastapi, uvicorn, pandas, lightgbm, ortools. Windows Smart App Control blocks new library files on their *first* load only; `start.bat` retries.
  - Real weather downloaded once into `data/weather/*.csv` (Open-Meteo; passes and sector from 1995, Leh from 1990, Kargil/Drass from 2010).
  - Written but **not run yet**: `backend/gen_data.py` (demo world, seed 42), `backend/adapters.py` + 7 configs in `sources/`, `backend/db.py`, `backend/app.py`, `backend/selfcheck.py`.
  - Written: `start.bat`, `reset_demo.bat`, `data/sector.json` (fictional posts inland), `data/params.json` (every number tagged FACTS / DERIVED / PLACEHOLDER).
  - Frontend scaffold (React + Vite + TS) builds; it currently has a placeholder page that lists the sources.

## Now / blocked
- Running `python -m backend.gen_data` (and the analog-year check that reads the weather files) was blocked by Claude Code's auto-mode safety check. Waiting for Atul to allow it.
- GitHub backup: waiting for Atul to create the private repo `RASAD` and sign in.

## Next
1. Choose the analog year (a past winter with snow on 20–24 Oct and again on 27 Oct–5 Nov) and set `demo.analog_year` in `data/params.json`.
2. Run `.venv\Scripts\python -m backend.gen_data`, then `.venv\Scripts\python -m backend.selfcheck`.
3. Start the app with `start.bat`, check that `http://localhost:8000` lists 7 sources, commit and push.
4. Step 3: forecasting.

## How to run
- Double-click `start.bat` (the first run sets things up). `reset_demo.bat` rebuilds the demo data.
- Dev mode for the UI: `cd frontend` then `npm run dev` (with the API running on :8000).
