# PROGRESS — RASAD

Read `BUILD_PROMPT.md` (the brief), `docs/PLAN.md` (the agreed plan, including the changes agreed on 5 Oct) and this file before continuing.
Backup: private GitHub repo https://github.com/AtulSharmx/RASAD. **After every step: commit, then `git push`.**

## Done
- **Step 0 (5 Oct 2026):** research in `docs/FACTS.md`, plan in `docs/PLAN.md`. Plan approved with changes: drone payload 15/20 kg, the Joint Primer (CICG / ILMS / IMMOLS) added, the IoT fuel-sensor feed is part of the base, GitHub backup.
- **Step 2 (5 Oct 2026):** setup, data, adapters.
  - Python 3.14 venv (`.venv`) with fastapi, uvicorn, pandas, lightgbm, ortools. LightGBM: use the native `lgb.train` API (scikit-learn is not installed). Windows Smart App Control blocks new library files on their *first* load only; `start.bat` retries.
  - Real weather in `data/weather/*.csv` (Open-Meteo; passes and sector from 1995, Leh from 1990, Kargil/Drass from 2010; real up to 4 Oct 2026). The free API allows ~5,000 calls/hour, so do not re-download casually.
  - After the last real day, weather is **simulated** by copying Oct 2021 onward (`demo.analog_year`). Oct 2021 was a real early-snow year: 22 cm on 23 Oct at the sector point, then clear and −15 to −22 °C.
  - `data/sector.json`: Leh, Kargil, Drass and the real passes; fictional roadheads Kilo and Lima, Node Mike, cols Sierra/Tango/Uniform, Posts Alpha–Hotel (inland, made-up coordinates).
  - `data/params.json`: every number tagged FACTS / DERIVED / PLACEHOLDER. `docs/PLACEHOLDERS.md` is generated from it.
  - `backend/gen_data.py` writes simulated feeds into `data/feeds/`, rebuilds `data/rasad.db` and loads 7 sources through `backend/adapters.py` (configs in `sources/`). Demo clock: **25 Oct 2026 06:00**.
  - Demo facts built in: Alpha kerosene ~8.7 days (sensor reading), Delta medical 3 days (track closed by snow since 23 Oct), Foxtrot rations 12 days (+20% troops since 20 Sep), Hotel's fuel sensor silent since 23 Oct 08:00. Three anomalies are injected, with ground truth in `data/anomaly_truth.json`.
  - `backend/selfcheck.py` passes. API: `/api/health`, `/api/sector`, `/api/stock`, `/api/sources`, `POST /api/sources/sync`. The frontend is still a placeholder page listing the sources.

- **Real data (5 Oct 2026, time-boxed):** `backend/realdata.py` caches three real sources: Open-Meteo 16-day forecast, Copernicus DEM (via the Open-Meteo elevation API) and OSM via Overpass (needs a User-Agent). 10 sources in total; each has a `label` (Real data / Simulated — military data is classified ...).
  - Node and pass heights in the DB come from the DEM (`gen_data` loads the real sources first, then builds the simulated world on top). The fictional sites were re-sited on real terrain.
  - `backend/world.py`: `clock(mode)`, `weather(location, mode)`, `stock(mode)`, `consumption(mode)`. Modes: `demo` (25 Oct 2026) and `live` (today + real forecast). **All later engines must read through world.py and take `mode`.**
  - API: `/api/health?mode=`, `/api/weather?location=&mode=`, `POST /api/live/refresh` (refreshes the forecast; 503 if offline), `/api/sector` now also returns OSM features.
  - Known limit: Live mode after 25 Oct 2026 has no simulated military data past that date, and the real archive is cached only up to 4 Oct 2026.

## Next
- Step 3: forecast per post per class (LightGBM quantiles vs a naive 28-day mean, held-out last 60 days), days of cover, accuracy in plain words. Add the checks to `backend/selfcheck.py`.

## How to run
- Double-click `start.bat` (the first run sets things up) and open http://localhost:8000. `reset_demo.bat` rebuilds the demo data.
- By hand: `.venv\Scripts\python -m backend.gen_data`, then `.venv\Scripts\python -m backend.selfcheck`.
- UI dev mode: `cd frontend`, then `npm run dev` (with the API running on :8000). After UI changes, `npm run build` (start.bat only builds when `frontend/dist` is missing).
