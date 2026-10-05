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

- **Step 3 (5 Oct 2026): forecast + days of cover** in `backend/forecast.py`.
  - LightGBM quantile models (P10/P50/P90) of daily use **per person**, one set per class. Inputs: post weather (sector_x minus a 6.5 °C/km lapse rate), altitude, day of year, post. × troop strength = demand. A `strength_factor` handles what-ifs.
  - Backtest on the last 60 days vs the naive "28-day average" (WAPE). Demo result: kerosene 10% vs 39%, rations 5% vs 11%, medical 28% vs 29%, batteries 17% vs 17%, clothing 32% vs 36%. P10–P90 band coverage 70–77% (slightly narrow; say so honestly).
  - Days of cover = days until the cumulative forecast passes the stock (P50; low = P90 demand, high = P10). Red < 7 / amber < 14 days (bad case), set in `params.json` → `cover`.
  - Demo: Alpha kerosene **4 days** (the naive average says ~9: a cold snap is coming), Delta medical 3 days (red), Foxtrot rations 11 days (amber) = **3 posts at risk**.
  - `forecast.run(mode)` is cached; it is cleared after a sync or a live refresh (`forecast.clear()`). Takes ~6 s per mode.
  - API: `/api/forecast?mode=` (accuracy + cover), `/api/forecast/{post}?mode=&days=`.
  - **Calibration (5 Oct 2026):** per class, `evaluate()` scores the LightGBM model against the 28-day average on a hold-out window and keeps whichever is clearly better (model must win by ≥1 point of WAPE, else the simpler naive method is used — kerosene, rations and clothing use the model; medical and batteries use the naive average). The winning method's P10–P90 band is then widened by the smallest factor that makes it cover ~80% of real days (`_calibrate`), fitted separately from the score so the reported accuracy stays honest. `/api/forecast` says so in its `note`.

- **Safety check (5 Oct 2026):** `backend/safety_check.py` (run by hand) checks every fictional site is ≥50 km from any real international boundary/LoC/LAC (Natural Earth lines, held in memory only, never saved or shown) and ≥5 km from any OSM-mapped military feature. Writes `docs/SAFETY_CHECK.md`; current result: all 14 fictional sites OK (60–97 km from boundary, 12.7–38 km from mapped military features).

## Next
- Step 4: Point of No Return (`backend/closure.py`). For each pass/col: fit a snowfall trigger to the real closure dates (FACTS §1), apply it to ~30 winters of real weather → closure-date distribution, shifted by this season's snow so far. Last safe dispatch = closure date at 80% confidence − transit − buffer. Show helicopter hours and the cost multiple after that date. Read through `world.py` and take `mode`.

## How to run
- Double-click `start.bat` (the first run sets things up) and open http://localhost:8000. `reset_demo.bat` rebuilds the demo data.
- By hand: `.venv\Scripts\python -m backend.gen_data`, then `.venv\Scripts\python -m backend.selfcheck`.
- UI dev mode: `cd frontend`, then `npm run dev` (with the API running on :8000). After UI changes, `npm run build` (start.bat only builds when `frontend/dist` is missing).
