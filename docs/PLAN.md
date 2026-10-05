# RASAD — Build plan (Step 0 output, waiting for OK)

## 1. How it runs
- **One process:** FastAPI serves both the API and the built React app at `http://localhost:8000`.
- `start.bat`: on first run it creates a Python venv, installs packages, builds the frontend, downloads and caches the weather, and creates demo data. After that it just starts the app and opens the browser.
- `reset_demo.bat`: regenerates the demo data (fixed seed) and clears approvals and the audit log.
- Fully offline after the first run. The UI footer says "Runs fully on-premise".
- Already installed on Atul's laptop: Python 3.14, Node 24, git. All libraries have wheels (checked with a dry run), so there is nothing to install by hand.

## 2. Folders
```
RASAD/
  start.bat  reset_demo.bat  README.md  PROGRESS.md  BUILD_PROMPT.md
  backend/
    app.py          FastAPI routes; also serves frontend/dist
    db.py           SQLite schema + helpers
    gen_data.py     synthetic sector, stock, consumption history (seed 42)
    weather.py      one-time Open-Meteo download -> data/weather/*.csv
    adapters.py     generic CSV/JSON adapter driven by sources/*.json
    forecast.py     LightGBM quantile model, naive baseline, days of cover
    closure.py      USP B: closure window + last safe dispatch date
    planner.py      USP A: OR-Tools CP-SAT mixed-fleet assignment + reasons
    drones.py       USP C: drone basing advisor
    scenarios.py    USP E: what-ifs (overrides -> re-run -> diff)
    selfcheck.py    one runnable check of the core logic
  sources/          one JSON config per data stream (USP D)
  data/
    fleet.json      payload/range/cost/weather limits per mode, each tagged SOURCE or PLACEHOLDER
    sector.geojson  offline basemap (roads, passes, tracks, rivers)
    feeds/          simulated CICG-like inventory + issues, IoT fuel-tank sensors (reading every 4 h),
                    BRO-like road status, IAF-like airlift schedule
    weather/        cached real Open-Meteo data
    rasad.db        SQLite (generated)
  frontend/         React + Vite + TS + Leaflet
  docs/             FACTS, PLAN, PLACEHOLDERS, EXPLAIN_SIMPLY, DEMO_SCRIPT
  screenshots/
```

## 3. Data model (SQLite)
| Table | Key columns |
|---|---|
| `nodes` | id, name, kind (depot / node / roadhead / post / helipad / drone_base), lat, lon, alt_m, troops, fictional |
| `links` | from, to, mode (road / jeep_track / mule_track / heli / drone), km, pass_id, status |
| `passes` | id, name, lat, lon, alt_m, axis, fictional |
| `stock` | post, class, qty, unit, as_of, source |
| `consumption` | date, post, class, qty (simulated history, 2 years, daily) |
| `weather` | date, location, tmin, tmax, snowfall_cm, snow_depth, wind_max, gust_max, cloud, wcode (real) |
| `forecast` | post, class, date, p10, p50, p90 |
| `recommendations` | id, kind (dispatch / PNR / drone basing), payload_json, status (pending / approved / modified / rejected) |
| `audit_log` | ts, role, user, action, rec_id, before_json, after_json, note |
| `source_runs` | source, ts, ok, records, error |

Supply classes: rations (kg), kerosene/fuel (litres), medical (kg), batteries/spares (kg), winter clothing (kg). No ammunition.

## 4. How the core logic works (short)
- **Forecast:** LightGBM with P10/P50/P90 quantiles. Inputs: troops, real temperature (adjusted for post altitude), altitude, day of year, recent consumption. Compared with a naive "last 28 days average" on a held-out last 60 days and explained in plain words. Days of cover = stock ÷ P50 daily demand.
- **Point of No Return:** for each pass/track, fit a snowfall trigger to the real closure dates in FACTS (recent years weighted more). Apply it to ~35 winters of real weather to get a closure-date **distribution**, then shift it by this season's (simulated) snow so far. Last safe dispatch = 80%-confidence closure date − transit days − loading buffer. After that date we show helicopter hours, cost multiple and risk.
- **Mixed-fleet planner:** CP-SAT decides how many sorties of each mode carry each load each day for 7 days. Rules: payload by altitude, range, weather windows, track status, fleet available, medical/urgent first. Goal: lowest cost + penalty for late delivery. Every line gets a reason built from the rule that decided it.
- **Drone advisor:** for N drones of a band, test each candidate base (posts within 15 km and the right altitude band), estimate the helicopter hours, porter/mule trips and stock-out risk saved over the winter (counting real flyable days), then place the drones greedily for the biggest saving.
- **What-if:** a scenario only changes inputs (closure −10 days, helicopters grounded 3 days, troops +20%, +20 drones), re-runs everything, and shows before vs after.

## 5. Screens (laptop 1366×768, calm ops-tool look)
1. **Dashboard** — map (depots, posts, roads, passes, tracks, helipads, drone legs) + KPI strip ("3 posts at risk", PNR alerts, helicopter hours needed) + post list with days-of-cover bars.
2. **Post detail** — forecast band per class, days of cover, accuracy vs naive.
3. **Point of No Return** — per post and class: closure probability curve, last safe dispatch date, cost after it.
4. **Mixed-fleet plan** — table + map legs + reason + cost; Approve / Modify / Reject.
5. **Drone advisor** — N and band input → ranked bases, savings.
6. **What-if** — 4 one-click scenarios, before/after.
7. **Sources** — health, last sync, record count, the config file shown.
8. **Audit log**.
9. (SHOULD) QM stock update with QR scan; consumption anomaly alerts.

Role switcher in the header: Commander / Logistics Officer / Post QM (demo only, no real login).

## 6. Demo story (data built around it)
Simulated date **25 Oct 2026**, "Sector X (fictional)". Rear nodes: Leh (main depot), Kargil, Drass (real public towns). Real axes: Zoji La (NH-1) and Manali–Leh (Baralacha La, Tanglang La). Forward: 8 fictional posts, **Alpha–Hotel**, at 4,100–5,400 m (real DEM heights at made-up inland spots), reached from fictional roadheads by jeep track or mule track. Some have helipads; Node Mike is a candidate drone base. The numbers below are **computed by the app** (updated 5 Oct 2026). Every cost multiple is shown with its inputs: truck Rs 1 lakh per 10 t and helicopter Rs 4 lakh per 45-min sortie (The Week, 2020), tagged PLACEHOLDER.
1. Dashboard → **3 posts at risk** (Alpha, Delta, Foxtrot).
2. **PNR alert:** "Post Alpha kerosene: last safe truck + jeep dispatch **29 Oct** (80% confidence). After that: air maintenance, **~220×** cost (road Rs 3.8/kg vs helicopter Rs 844/kg; inputs as above; PLACEHOLDER)."
3. **Plan:**
   - "Medicines to Post Delta by drone: **274 kg in 19 sorties on 26 Oct** from Roadhead Lima (8.5 km, 15 kg per sortie). The track is closed by snow; a helicopter + porters would be ~Rs 1,344/kg vs ~Rs 106/kg (**~13×**)."
   - Alpha kerosene goes by jeep and mule before 29 Oct.
   - Foxtrot rations go by mule and porter today, then 30 helicopter sorties.
4. **Drone advisor (headline):** "20 drones (12,000–20,000 ft band) at **Node Mike**: helicopter sorties to Post Foxtrot drop from **30 to 0** this week, and **₹167 lakh** is saved (33.8 helicopter hours). Today Foxtrot is out of drone reach: the only drones are at Roadhead Lima, 19 km away (range 10 km)."
5. **What-ifs** (before → after this week):
   - Pass closes 10 days early: posts at risk 3 → 4 (Echo), helicopter sorties 30 → 49, 27.5 t cannot move.
   - Blizzard grounds helicopters 3 days: 3.9 t cannot move.
   - Troops +20% at Alpha–Charlie: posts at risk 3 → 5 (Bravo, Charlie).
   - 20 drones arrive: helicopter sorties 30 → 0, cost ₹1.84 crore → ₹0.17 crore.
6. **Sources** page → add a config file → a new stream appears.
7. **Commander approves** → audit log entry.

## 7. Build order (7 days; steps 3–6 matter most)
| Day | Work |
|---|---|
| 1 (5 Oct) | Step 0 ✓ · Step 2: setup, git, weather download, data generator, adapters, DB, start scripts |
| 2 | Step 3 forecast + accuracy · Step 4 Point of No Return |
| 3 | Step 5 mixed-fleet planner · Step 6 drone advisor + what-ifs |
| 4–5 | Step 7 all UI screens (design skills) · Step 8 sources, approvals, audit |
| 6 | Step 9 SHOULD items if time (anomaly alerts, QM QR page) |
| 7 | Step 10 polish, self-check, screenshots, README, EXPLAIN_SIMPLY, DEMO_SCRIPT, dry run |

`PROGRESS.md` is updated and a git commit is made after every step.

## 8. Changes agreed on 5 Oct 2026
- Drone payload: **15 kg** for 12,000–20,000 ft and **20 kg** for 6,000–12,000 ft; range 10 km (Tribune, Oct 2022 RFP).
- **IoT is part of the base, not SHOULD:** simulated fuel-tank level sensors at posts, one reading every 4 h. It is a normal source adapter, shown on the Sources page, and it updates kerosene stock. The QM QR page stays in SHOULD.
- Army system named **CICG** (Joint Primer, Aug 2025).
- Private GitHub repo `RASAD`; push after every step.

- **Real-data rule (5 Oct):** use real public data wherever it is free and needs no account. Military data stays simulated and is labelled "Simulated — military data is classified; in deployment this comes from CICG via adapters". Real sources added: the Open-Meteo 16-day forecast (**Live mode**), Copernicus DEM heights, and OSM roads/passes/towns. Each is its own source, marked "Real data". Anything that needs an account, a key, or a paid/free-tier plan → ask first.
- **Modes:** `demo` (clock 25 Oct 2026, simulated outlook) and `live` (clock = today, real forecast). Every engine takes `mode` and reads through `backend/world.py`.

## 9. Skipped on purpose
No Docker, Postgres, Redis, Celery or real auth. Configs are JSON (no YAML library needed). No truck *routing* (VRP): the problem here is *which mode*, not *which street*.
