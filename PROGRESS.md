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

- **Fixes before Step 4 (5 Oct 2026):**
  - Band calibration: a band-widening factor is chosen on the 60 days *before* the hold-out, then scored on the hold-out. Coverage is now 76–86% (it was 70–77%). The live forecast uses a factor re-fitted on the latest 60 days.
  - Per class, the better method on the hold-out is used: model or 28-day average (the model must win by ≥1 percentage point). Kerosene, rations and winter clothing → model; batteries and medical → 28-day average. `/api/forecast` returns `method` and `why` for the screen.
  - Safety: `python -m backend.safety_check` → `docs/SAFETY_CHECK.md`. Natural Earth boundary lines are used in memory only (never saved or shown). Every fictional site is ≥54 km from any boundary/LoC/LAC (posts ≥60 km) and ≥12.7 km from any military feature mapped in OSM. ALL OK.
  - Git: `credential.helper manager`. Run `git push` **without** a `timeout` wrapper (the login window needs it), ideally in the background.

- **Step 4 (5 Oct 2026): Point of No Return** in `backend/closure.py`. Real closure dates are in `data/closures.json`.
  - Rule fitted on REAL closures: a route closes when (snow so far ≥ C AND 3-day snow ≥ D) OR the 7-day mean temperature ≤ T.
    - Zoji La: C=210 cm, D=20 cm, T=−15.5 °C (a snow pass); fit error 5.4 days, leave-one-winter-out 12.6 days (n=5).
    - Manali–Leh (Baralacha): D=44 cm, T=−15.5 °C (a cold/ice pass); fit error 7.5 days, leave-one-out 17.8 days (n=4).
  - This season so far (+ the real forecast in Live mode) is replayed against 31 real past winters (1995–2025) → closure-date distribution. Last safe dispatch = 20th percentile closure (80% still open) − transit − 1 day buffer. Storms before today do not count; the road feed already tells us whether they closed the route.
  - Forward roads and tracks use the Manali–Leh rule at their highest point (temperature lapse rate), with PLACEHOLDER snow-threshold factors (road 0.8, jeep 0.5, mule 0.4) and reopening 30 days after Manali–Leh.
  - After the PNR: helicopter from Leh (payload by helipad height, ~Rs 4 lakh per 45 min), with porters when the post has no helipad; cost per kg vs the road; ~72% of past winter days were inside the helicopter weather limits.
  - Winter stock: non-short items are stocked until 15 Jun 2027 (+5–20%), so only the 3 designed items are short. Charlie's medical surge was moved to 8–14 Sep (outside the 28-day window).
  - Demo result: Manali–Leh closes 2 / 13 / 24 Nov (P20/50/80); Zoji La 10 Dec / 31 Dec / 12 Jan. Alpha kerosene: last safe truck + jeep dispatch **29 Oct** (80%), then ~220× cost (40 t → 77 sorties, ~Rs 3.4 crore). Foxtrot rations: last safe dispatch **today (25 Oct)**. Delta medical: track closed → **air only now** (drones next).
  - API: `/api/pnr?mode=` (items, axes, daily P(closed) curves per post). Self-check covers it.

- **Fixes before Step 5 (5 Oct 2026):**
  - No selection leak: the method and band factor are chosen on the earlier 60 days (27 Jun–25 Aug); the score comes only from the final 60 days (26 Aug–24 Oct). Now only kerosene uses the model (select window 8.5% vs 55%; test 9.0% vs 39.3%). Rations, clothing, medical and batteries use the 28-day average. Test coverage is 79–89%.
  - Every cost multiple carries its inputs: `closure.cost_basis()` text + `cost_inputs` (truck Rs 1 lakh per 10 t, helicopter Rs 4 lakh per 45-min sortie, The Week 2020, PLACEHOLDER). The "~40×" wording in `docs/PLAN.md` was replaced with computed numbers.
  - New PNR status `margin`: a winter gap smaller than 14 days of current use (`closure.margin_days`) is inside the forecast error, so it is flagged for review, not urgent. This is needed because the 28-day average stretches October's clothing issue season over the whole winter.
- **Step 5 (5 Oct 2026): mixed-fleet planner** in `backend/planner.py` (OR-Tools CP-SAT, 7-day horizon, deterministic).
  - Loads are the PNR items with status passed/urgent. Options: truck/jeep (to road/jeep-track posts), mule, porter, helicopter (Leh → helipad, or nearest pad + porters), drone (bases in `fleet.drones_at`; range 10 km; leg must clear DEM terrain + 400 m below the 20,000 ft ceiling; 15 kg in the high band).
  - Rules: ground options only on days ≤ last safe dispatch and never on a closed route. Fleet limits: jeeps 12/day, trucks 10 × 2.5 t/day, mules/porters per roadhead using round-trip days, helicopter hours from the airlift allotment on flyable days, drone minutes and battery cycles per base. Weather windows come from `world.weather` (helicopter: gust ≤55, snow ≤2, cloud ≤85; drone: gust ≤35, snow ≤1; all PLACEHOLDER).
  - Objective: cost + a penalty for undelivered kg + a delay penalty (×10 after the post would run out). The penalties are team choices in `params.json` → `planner`.
  - Demo plan (Rs 1.84 crore in total):
    - Delta medicine 274 kg by drone, 19 sorties on 26 Oct (drones grounded on 25 Oct by snow), ~13× cheaper than helicopter + porters.
    - Alpha kerosene: ~38 t by jeep on 25–28 Oct plus 1.7 t by mule.
    - Foxtrot rations: 800 kg by mule and 220 kg by porter today, then 11.9 t in 30 helicopter sorties (drones 19 km away, out of range).
    - Alpha clothing 252 kg by jeep. Echo clothing is on "watch".
  - Each line has a summary, a plain reason, a cost and assumptions with tags (PLACEHOLDER / public source).
  - **Commander in the loop:** tables `decisions` and `audit_log`. `POST /api/plan/decision` takes `{key, action: approve|modify|reject, role, user, kg?, note?}`. Approve/reject is for the Commander only; modify is for the Commander or the Logistics Officer; the Post QM gets 403. Every action goes to `GET /api/audit`. Approving a modified line keeps the modified kg. `reset_demo.bat` clears decisions.
  - API: `GET /api/plan?mode=` (cached solve + fresh decisions). The self-check covers all of the above, then removes its own test decisions.

- **Fixes before Step 6 (5 Oct 2026):**
  - **One set of cost inputs:** `backend/costs.py` + `params.json` → `costs` (source The Week 2020, all PLACEHOLDER). The PNR, planner, drone advisor and what-ifs all price through it; `/api/costs` serves it. The rate is per kg-km, so Srinagar–Leh = ₹10/kg and Alpha's 100 km forward route = ₹3.8/kg. FACTS §5 explains this.
  - **Drone realism:**
    - Each sortie's flight time is checked against the 40-min endurance.
    - One sortie ties a drone up for max(flight + 5 min swap, (flight + 90 min recharge) / 2 batteries) = ~55 min for Delta. Each base's drones fly at most 8 h/day; the planner splits loads across days when needed.
    - Plan lines show a daily schedule: "26 Oct: 19 sorties = 4 drones x up to 5 sorties, 19 battery charges".
    - PLACEHOLDERs: `swap_min`, `batteries_per_drone`, `charge_min`, `op_hours_per_day`.
  - Bug found and fixed: a name clash (`shift`) in `closure.segment` had moved closure days by the temperature correction.
- **Step 6 (5 Oct 2026): drone advisor + what-ifs.**
  - `backend/drones.py` `advise(mode, n, band)`:
    - Re-plans with N extra drones at each roadhead/node (bases supplied by road) and ranks the bases by ₹ saved, helicopter sorties/hours and foot trips.
    - Headline: Foxtrot helicopter sorties 30 → 0 with 20 drones at Node Mike, ₹167 lakh saved.
    - Lower-band drones cannot clear the terrain and save nothing.
  - `backend/scenarios.py`: 4 what-ifs (pass −10 days via `closure.run(shift=-10)`, blizzard via `planner.plan(grounded_days=3)`, troops +20% via `closure.run(strength=...)`, 20 drones at the best base). Each returns before/after KPIs and plain change lines, with a note when the cost falls only because loads did not move.
  - API: `/api/drones?mode=&n=&band=`, `/api/scenarios?mode=`, `/api/costs`. A background warm-up at server start pre-computes the demo; cold calls take ~25–30 s.

- **Step 7 + 8 (6 Oct 2026): the UI**, design-first with impeccable + frontend-design + make-interfaces-feel-better + dataviz.
  - `PRODUCT.md` (confirmed: real-Army-tool first, English only, "RASAD रसद"). Two directions were shown as dashboard screenshots (`docs/design-directions/`). Atul chose **A "Strip Bay"** (IAF flight-progress strips), with B's toposheet map on the dashboard. The direction contract is in `.impeccable/surfaces/frontend-src-app-tsx.md`; `DESIGN.md` + `.impeccable/design.json` record the built system.
  - React app (`frontend/src`):
    - `App.tsx` shell: top rail with Demo/Live, Guided demo and role picker; nav rail; bottom rail with closure windows, source health and on-premise.
    - `SectorMap.tsx`: offline Leaflet map with the real DEM relief, 200 m contours, OSM roads, legend, scale bar and red numbered rings.
    - `ui.tsx`: provenance chips with popovers; mode holders with icon + word (helicopter and drone glyphs authored in Lucide style).
    - `charts.tsx`: forecast band chart and closure curve, with hover.
    - Screens: Dashboard, PostDetail, Pnr, Plan (Approve/Modify/Reject by role), Drones, WhatIf (flip cells), Sources (config viewer, sync, live refresh), Audit.
    - `GuidedDemo.tsx`: 7 moments, Next/Back/Esc, spotlight, a data-driven "Say" line. `#/dashboard?demo=3` opens moment 3.
  - Mode colours validated with the dataviz script: road #a86b00, foot #00917f, heli #2d5fc4, drone #b0428f. Status colours are reserved.
  - Backend: `/api/terrain`. The DEM grid now covers 33.80–34.45 N, 76.35–77.65 E (3,848 points). `index.html` is sent with `no-cache`.
  - Audit (impeccable): the detector's layout-animation finding was fixed. The one remaining finding is a false positive (the legend line swatch). Also fixed: white-on-ochre contrast (3.4 → 4.4:1), a stacked layout below 1100px, rupee formatting, and the demo text.
  - Screenshots: `screenshots/01-…12-` (all 8 screens at 1366×768, the dashboard at 1920×1080, guided demo moments 1 and 3).

- **Step 10 (6 Oct 2026): docs and dry run.**
  - `README.md` (one-click start, demo roles, Real / Simulated / PLACEHOLDER), `docs/EXPLAIN_SIMPLY.md` (Hinglish, 22 jury questions with English one-liners), `docs/DEMO_SCRIPT.md` (3-minute script matching the 7 Guided demo moments, plus a 1-minute version), `docs/TROUBLESHOOTING.md` (Hinglish).
  - `start.bat`: opens the browser if RASAD is already running; runs `npm install` only when `node_modules` is missing (an offline fresh build works).
  - `reset_demo.bat`: refuses while RASAD is running; `db.init` gives a clear message if the database is locked. Live refresh offline returns "No internet connection. RASAD keeps using the saved forecast (downloaded …)".
  - **Dry run (internet blocked for RASAD with a dead proxy):**
    - Deleted the DB and `frontend/dist`, then ran `start.bat`: it built, generated the data and served in about 1 minute.
    - All 7 Guided demo moments checked (screen, spotlight, Say line). Approve → audit row.
    - `reset_demo.bat` while running → refused; after stopping → reset in ~4 s; `start.bat` again → audit empty, all 8 plan lines pending.
    - Double `start.bat` → just opens the browser. Live mode offline → works from the cached forecast (11 s).

- **Step 9 (6 Oct 2026, lean): data alerts** in `backend/anomaly.py`, `/api/alerts`, an Alerts screen (nav item and a dashboard link).
  - Expected use per person = LightGBM median model (weather, height, season, post). r = log(actual/expected); noise = robust MAD per series.
  - One-day spike (> 5 noise widths and ≥ 3×) → likely data error. A 7-day median ≥ 2 noise widths and ≥ 1.2× → steady excess (< 2×, possible leak/pilferage) or sharp surge (≥ 2×, confirm with the post). Silent IoT sensors come from the adapter health.
  - Result on demo data: exactly the 3 injected anomalies (Bravo rations data error, Hotel kerosene steady excess 1.37×, Charlie medical surge 3.1×) plus Hotel's silent sensor, and no false alarms. The self-check verifies this against `data/anomaly_truth.json`. The QM QR page was skipped (as agreed).

## Known limits (say these honestly)
- **Roles are demo-only.** The brief asks for demo roles with no real login, so `role` and `user` come from the request (the role picker). Anyone who can reach the API can claim "Commander". Mitigations: the server listens only on 127.0.0.1, and FastAPI parses only JSON bodies, which blocks simple cross-site form posts. Production would take the identity from Army SSO/PKI and map roles on the server. An automated security review flagged this on 5 Oct; it was acknowledged and documented, not fixed (by design for the demo).

- The UI is built for laptop and projector (1366–1920 wide); below 1100px it stacks, but there is no phone layout.
- Live mode recomputes everything on first use (~30–60 s); Demo mode is pre-computed at server start.

## Next
- Nothing required. Optional: rehearse with `docs/DEMO_SCRIPT.md`; add screenshots to the PPT from `screenshots/`.

## How to run
- Double-click `start.bat` (the first run sets things up) and open http://localhost:8000. `reset_demo.bat` rebuilds the demo data.
- By hand: `.venv\Scripts\python -m backend.gen_data`, then `.venv\Scripts\python -m backend.selfcheck`.
- Guided demo: press **Guided demo** in the top bar (or open `http://localhost:8000/#/dashboard?demo=1`). ←/→ to move, Esc to close.
- UI dev mode: `cd frontend`, then `npm run dev` (with the API running on :8000). After UI changes, `npm run build` (start.bat only builds when `frontend/dist` is missing).
