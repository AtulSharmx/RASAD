# RASAD verification report

Read-only check, 6 Oct 2026. The project code, data and config were not changed and nothing was committed. All experiments ran on a temporary copy of the project outside the repo, which was deleted afterwards. This file is the only thing written into the project.

> **Status after the honesty patch (6 Oct 2026, same day).** The report below is the snapshot *before* the patch.
>
> **Fixed (wording and UI only; data, story and numbers unchanged):**
> - Hardcoded presenter, dashboard and drone texts (finding 4).
> - The "learned from real closure dates" overclaim; the forward-track PLACEHOLDER rule is now stated (finding 3).
> - The accuracy caveat is shown next to every accuracy number (finding 1 is now disclosed).
> - The "no false alarms" claim (finding 6).
> - The planner time-limit notice, the "Sync all now" warning plus background recalculation, and pinned library versions (finding 8).
> - Docs (section 5).
>
> **Still true by design** (disclosed, not changed):
> - The circular accuracy (1) and the planted scenario (2).
> - The placeholder drone economics (5) and the small closure-date sample (7).
> - The Live-mode clock mix (9) and the planner realism gaps (10).

## Verdict: PARTLY REAL

**The engine is real. The demo scenario around it is staged, and some headline claims (forecast accuracy, "learned from real closure dates", "no false alarms") are stronger than the evidence.**

What is real:
- Every number on screen is computed at run time from the database.
- LightGBM is really trained. OR-Tools really solves the plan.
- Closure windows really come from 31 winters of real weather.
- When I changed an input, the outputs moved the right way every time (section 6).

What is not real or not proven:
- **The three "at-risk" posts are planted** in the simulated stock.
- **Delta's closure** is a hand-written line in the simulated road bulletin.
- **The drone answer is set up by the map.** Node Mike is a fictional point placed 9 km from Foxtrot.
- **The forecast is graded on data generated from the same formula it learns.** That makes "9% vs 39%" circular.
- **Several sentences the presenter reads are fixed text**, not calculations.

---

## 1. Every source file: what it does, and whether it is used

Skipped as instructed: `.venv`, `node_modules`, `frontend/dist`, the weather, terrain and forecast caches, generated feeds, `rasad.db`, screenshots, and design mock-ups.

### Backend (`backend/`)

| File | What it does | Used? |
|---|---|---|
| `__init__.py` | Empty package marker | Yes (imports) |
| `adapters.py` | Reads each `sources/*.json` config: renames columns, translates codes, refuses unknown codes, loads into SQLite, and reports health and staleness | Yes: data build, Sync button, Sources page, alerts |
| `anomaly.py` | Fits a LightGBM median "expected use per person" model. Flags one-day spikes and multi-day excess or surges, and lists silent IoT sensors | Yes: `/api/alerts` |
| `app.py` | FastAPI API plus the built web app. Background warm-up, no-cache rule for the page | Yes: the server |
| `cache.py` | `memo()`: result cache in which a second caller waits for an in-progress calculation instead of starting another | Yes: 6 modules |
| `closure.py` | Fits a snow/cold closure rule to real dates and replays 31 real winters. Computes the last safe dispatch per post and supply, plus the air cost after it | Yes: `/api/pnr`, planner, what-ifs |
| `costs.py` | The single set of cost rates and cost helpers | Yes: everywhere costs appear |
| `db.py` | SQLite schema, connect and query; loads `sector.json` | Yes |
| `drones.py` | Re-runs the planner with N drones at each candidate base and ranks the bases | Yes: `/api/drones`, what-ifs |
| `forecast.py` | LightGBM quantile model vs a 28-day average: picks the method per class on an earlier window, calibrates the band, and computes days of cover | Yes |
| `gen_data.py` | Builds the simulated world (fixed seed), writes the feed files, loads all sources, and regenerates `docs/PLACEHOLDERS.md` | Yes: `start.bat` (first run), `reset_demo.bat` |
| `planner.py` | OR-Tools CP-SAT 7-day mixed-fleet plan, line reasons, and Approve/Modify/Reject with the audit log | Yes |
| `realdata.py` | Downloads and caches the Open-Meteo forecast, Copernicus DEM and OSM (only if missing) | Yes: data build, Live refresh, `/api/terrain` grid |
| `safety_check.py` | One-off distance check of the fictional sites against boundaries and mapped military features; writes `SAFETY_CHECK.md` | Manual only, not at run time |
| `scenarios.py` | The 4 what-ifs (closure −10 days, blizzard, troops +20%, +20 drones) | Yes |
| `selfcheck.py` | Asserts the demo story and core rules | Manual only. **It is tied to the seed-42 story and fails on other data** (section 6) |
| `weather.py` | Open-Meteo archive downloader and a polite `fetch_json` | Yes: data build (only if missing), `realdata` |
| `world.py` | Demo/Live clock, weather source priority, consumption, Live-mode stock add-back | Yes. The `MODES` constant is **unused** |

### Frontend (`frontend/src/` and config)

| File | What it does | Used? |
|---|---|---|
| `main.tsx` | Entry point, fonts, CSS | Yes |
| `App.tsx` | Shell, navigation, Demo/Live switch, role picker, footer (closure windows, source health) | Yes |
| `api.ts` | Fetch helper, session cache, formatting, "worst item per post" summary | Yes |
| `ui.tsx` | Icons, chips (Real/Sim/PLACEHOLDER), badges, loading and error boxes | Yes |
| `charts.tsx` | Forecast band chart, closure-probability curve | Yes (Posts, Point of no return) |
| `SectorMap.tsx` | Leaflet map: DEM relief and contours, OSM highways, fictional posts and tracks | Yes (Dashboard only) |
| `GuidedDemo.tsx` | 7-moment presenter overlay with "Say" lines | Yes. **Part of its text is fixed** (section 5) |
| `app.css` | All styles | Yes |
| `screens/Dashboard.tsx` | Map plus at-risk strips | Yes |
| `screens/PostDetail.tsx` | Per-post table, forecast chart, accuracy text | Yes |
| `screens/Pnr.tsx` | Point of no return list, closure curve, rear axes | Yes |
| `screens/Plan.tsx` | Plan lines with Approve/Modify/Reject | Yes |
| `screens/Drones.tsx` | Drone advisor | Yes |
| `screens/WhatIf.tsx` | Before/after table | Yes |
| `screens/Alerts.tsx` | Data alerts | Yes |
| `screens/Sources.tsx` | Source health, config viewer, Sync and Live refresh | Yes |
| `screens/Audit.tsx` | Audit log | Yes |
| `index.html`, `package.json`, `vite.config.ts`, `tsconfig*.json` | Build setup | Yes |
| `.oxlintrc.json` | Lint config (`npm run lint`); not part of the build | Rarely |
| `public/favicon.svg` | **The default Vite logo** (purple lightning bolt), not a RASAD icon | Yes (browser tab) |

### Data, sources, scripts, docs

| File | What it does | Used? |
|---|---|---|
| `data/sector.json` | Fictional posts, roadheads, cols and tracks, plus the real towns and passes | Yes |
| `data/params.json` | Every tunable number, with a FACTS / DERIVED / PLACEHOLDER tag | Yes |
| `data/closures.json` | Real closure/reopening dates (Zoji La 5 winters, Baralacha 4) | Yes: closure fit |
| `data/anomaly_truth.json` | Ground truth of the injected anomalies (written by `gen_data`) | Selfcheck only |
| `sources/*.json` (10 files) | One adapter config per stream. Real: `open_meteo_weather`, `open_meteo_forecast`, `copernicus_dem`, `osm_geometry`. Simulated: `cicg_stock`, `cicg_issues`, `iot_fuel_sensors`, `bro_road_status`, `iaf_airlift`, `met_outlook` | Yes, all 10 |
| `start.bat` | One-click start: setup on first run, retry for Smart App Control, build, data, server | Yes |
| `reset_demo.bat` | Rebuilds the demo data; refuses while RASAD is running | Yes |
| `requirements.txt` | Python packages, **with no versions pinned** | Yes (first run) |
| `.claude/launch.json` | Dev preview config | Development only |
| `.gitignore`, `.gitattributes` | Git rules (CRLF for `.bat`) | Yes |
| `.impeccable/*` | Design-tool files | Not at run time |
| `README.md`, `PRODUCT.md`, `DESIGN.md`, `PROGRESS.md`, `CLAUDE.md`, `BUILD_PROMPT.md` | Team docs | Docs |
| `docs/FACTS.md` | Public facts with links and a confidence level for each | Docs (basis for `params.json` and `closures.json`) |
| `docs/PLAN.md` | The Step-0 plan. **Stale**: it says the forecast uses troops and recent consumption, and that the drone advisor plans the whole winter and places drones greedily. Neither is true | Docs |
| `docs/PLACEHOLDERS.md` | Generated list of placeholder numbers | Docs |
| `docs/SAFETY_CHECK.md` | Generated distance check (5 Oct) | Docs |
| `docs/EXPLAIN_SIMPLY.md`, `docs/DEMO_SCRIPT.md`, `docs/TROUBLESHOOTING.md` | Team and jury docs | Docs (claims checked in section 5) |

There are no TODO or FIXME markers. Three marked shortcuts (`ponytail:` comments) exist:
- planner: one truck round trip per day;
- planner: mule and porter limits are checked as weekly totals;
- world: Live-mode stock assumes no deliveries.

---

## 2. Fake or real? Feature by feature

| Feature | Calculated at run time? | What is staged or hardcoded around it |
|---|---|---|
| **Forecast** | **Yes.** 3 quantile models × 5 classes are trained every time the cache is empty. Method and band are chosen on 27 Jun–25 Aug and scored on 26 Aug–24 Oct. **LightGBM is used for kerosene only**; the other 4 classes use the 28-day average, which ignores weather entirely (test 5). | **Circular accuracy.** `gen_data.py` makes kerosene use = 1.0 L + 0.12 L × (degrees below +10 °C at the post's height), with about 10% random noise. The model gets exactly that temperature as an input, so its 9% error is just the noise we injected. "9% vs 39%" proves the code works, not that the forecast would work on real data. |
| **Days of cover** | **Yes**: cumulative P10/P50/P90 demand vs stock. | The 3 short items are **planted**: `SHORT = {Alpha kerosene: 9 days, Delta medical: 3 days, Foxtrot rations: 12 days}` sets their stock. All other stock is 5–20% above the simulated winter need. |
| **Point of No Return** | **Yes.** A rule (C, D, T) is grid-searched on real closure dates. The season is then replayed against 31 real ERA5 winters, and the 20th percentile gives the 80% date. | **(a)** Delta's "air only" comes from a hand-written bulletin line, `RHL-PD: CLOSED`. **(b)** The forward roads and tracks that set every post's deadline are **not fitted to any real track**. They reuse the Manali–Leh rule, scaled by PLACEHOLDER factors: 0.8 road, 0.5 jeep, 0.4 mule, +30% snow per 1,000 m, and a 30-day reopening lag. **(c)** The fit uses only 5 Zoji La and 4 Baralacha dates. 3 of the 4 Baralacha dates are rated "Low" in FACTS (one travel website). The "High"-confidence 8 Dec 2025 date was **not** used; a "Low–Medium" 20 Nov 2025 date was. |
| **Mixed-fleet plan** | **Yes.** It is a real CP-SAT model with integer trips and kg per load, mode and day. Constraints cover fleet limits, helicopter hours, drone flight cycles and the deadline. Status is OPTIMAL on the demo data. With heavy inputs it hits the 20-second limit and returns FEASIBLE (not proven optimal), and **the UI does not show this**. Test 6 shows real re-optimisation. | **Realism gaps:** <ul><li>Track status "restricted" is ignored. Alpha's track is "one-way, chains required", yet 48 jeep trips are planned.</li><li>Truck, jeep and mule capacity are simplified.</li><li>The helicopter payload curve is a PLACEHOLDER.</li></ul> |
| **Drone advisor** | **Yes.** The full planner is re-run per candidate base. Savings shrink sensibly as N falls (test 4). | **(a)** The winning base, Node Mike, is a fictional point placed 8.9 km from Foxtrot, just inside the 10 km range. **(b)** The ₹1.67 crore saving needs **809 drone sorties in one week** from that one node. It rests on PLACEHOLDER drone cost (₹1,500 per sortie), 2 batteries, 90-min recharge and 8 flying hours a day. **(c)** About 12 t is assumed to reach Node Mike by road, with no jeep-capacity or track-closure check. **(d)** The headline is **hardcoded to Foxtrot** and to the sentence "the only drones are at Roadhead Lima, 19 km away". |
| **What-ifs** | **Yes.** Each re-runs the Point of No Return and the plan with changed inputs (test 8). The cost note "not a saving" when loads are left behind is honest. | Built-in scenarios only. |
| **Alerts** | **Yes.** Removing the injected anomalies removes the alerts (test 7). | The thresholds were tuned on the demo data. On 3 other seeds, **each run gave 1 false alarm**. The "expected use" model is the same formula that generated the data, which makes detection easier than it would be on real data. |
| **Sources / adapters** | **Yes.** Configs are really read; unknown codes are really refused (selfcheck); a silent sensor really falls back to CICG. | The feeds are static files written by `gen_data`, not live connections. The CICG, BRO and IAF formats (column names like `ISSUE_DT`, `UNIT_LOC_CODE`, `SKO`) are **invented**. "New stream = one file, no code" only holds if the data fits one of the 7 existing tables. |
| **Approvals / audit** | **Yes.** Server-side role check, decision table, audit rows with before/after, user and time. | The role is whatever the browser sends (documented as demo-only). The audit log is a plain SQLite table: anyone with the file can edit it. |

---

## 3. Data: real, simulated, placeholder

**Real (public, free, no account):**
- **Open-Meteo ERA5 archive** for 7 points, 1995 (towns 1990/2010) to **4 Oct 2026**, 72,068 rows.
  - Spot-checked against the live API: Leh, 20–24 Oct 2021, is **identical** (for example 8.61 cm snow on 23 Oct).
  - Note: ERA5 is a **reanalysis (weather-model) product at ~10–25 km**, not station measurements. `sector_x` is a grid point with elevation forced to 4,000 m.
- **Open-Meteo 16-day forecast**, cached 5–20 Oct 2026 (Live mode only).
- **Copernicus DEM GLO-90** via the Open-Meteo elevation API: 3,848 points, all node heights.
- **OpenStreetMap**: NH-1/NH-3, passes, Leh/Kargil/Drass. 622 features, fetched 5 Oct.
- **Closure/reopening dates** from news and travel sites (FACTS §1). Quality is mixed; see section 2.
- **Public figures**: drone RFI numbers (2,715 drones; 15/20 kg; 10 km), Sabal 20 specs, mule 40 kg, porter 20 kg, The Week 2020 cost quotes, Dhruv 200 kg.
- **Natural Earth boundaries and OSM military features**, used only by `safety_check.py`.

**Simulated (labelled in the UI):**
- Posts, roadheads, cols, Node Mike, tracks and their lengths.
- Troop strength, stock, consumption history, IoT readings, road bulletin, helicopter allotment.
- Injected anomalies, the Foxtrot +20% strength change, Hotel's silent sensor.
- All weather after 4 Oct 2026: a copy of 2021, relabelled as 2026.

**PLACEHOLDER (made up, tagged):**
- Consumption rates, fleet sizes, speeds, weather limits, drone batteries and cost.
- Helicopter payload curve (except one public point).
- Forward-track closure factors.
- All costs. Truck and helicopter come from one retired officer's 2020 quote; jeep ×4, mule, porter and drone are invented.

**Real-looking but made up** (point these out to the jury before they assume otherwise):
- **Post heights** (Delta 5,401 m and so on) are real DEM heights at *fictional* coordinates.
- **The "current" demo weather**, including the 22.5 cm snowfall on "23 Oct 2026", is real *2021* weather moved to 2026.
- **The CICG/BRO/IAF export formats** (column names, item codes such as `SKO`, sortie IDs `HX-…`) are guesses, not the real system formats.
- **The road bulletin text** ("Fresh snow 20 cm at Col Uniform. One-way, chains required.") and the IoT sensor IDs and battery voltages are written by `gen_data.py`.
- **Exact-looking cost rates** (₹0.024/kg-km, ₹5.33 lakh/h) are back-of-envelope derivations from one quote.
- **Track lengths** in `sector.json` (for example Lima–Foxtrot 27 km) are invented.
- **Accuracy figures** (9%, 79–89% band coverage) are measured on simulated data generated by our own formula.

---

## 4. Quality: bugs, shortcuts, demo risks, mismatches

**Bugs and wrong behaviour**
1. **Guided demo moment 1:**
   - The title is the fixed text "Three posts at risk". With seed 7 there are 4 at-risk posts.
   - If no post is at risk, the code falls back to saying "Three" (`risk.length || 'Three'`).
2. **Guided demo moment 3:** "about twelve times cheaper than a helicopter" and "Alpha's kerosene goes by jeep before its deadline" are fixed text. They are true today (12×, jeep), but they do not follow the data.
3. **Drone advisor headline** (`drones.py`):
   - It is always about Post Foxtrot.
   - It always includes "the only drones are at Roadhead Lima, 19 km away (range 10 km)", even for N = 1 ("1 drones") or other settings.
4. **Dashboard text:**
   - Every "passed" item shows "Track closed by snow". "Passed" also means "will close before a convoy can arrive". In the colder or −10-day tests, Alpha and Foxtrot became "passed" with open tracks, and the strip would wrongly say "closed by snow".
   - "15 kg each" is fixed text.
5. **"Restricted" road status is ignored** by both the closure logic and the planner.
6. **Live mode mixes clocks:**
   - The 25-Oct bulletin (Delta closed) and the 25-Oct-based stock are applied to today.
   - Source health and "sensor silent for 46 h" use the demo clock, not the live one.
   - Once today passes 20 Oct, the cached "real" forecast is out of date. Live mode then falls back to the simulated 2021 copy without saying so.
7. **The planner can return a non-optimal plan** (20-second limit; seen with troops ×1.5). The UI never shows the solver status.
8. **`selfcheck.py` checks the demo story, not general correctness.** On seed-7 data it fails ("exactly PA, PD, PF at risk"). "selfcheck OK" means "the story is intact", nothing more.

**Risky shortcuts and live-demo risks**
- **"Sync all now"** is on the Sources screen (guided moment 6). It clears every result cache, so moment 7 (Plan) then takes ~15–30 s to recompute. **Do not press it during the demo.**
- **Live switch:** 30–60 s the first time.
- **Drones page:** any new N or band runs 3 full re-plans (up to about a minute).
- **First start:** ~13 s before the dashboard fills, even after the pile-up fix.
- **`requirements.txt` has no versions.** A fresh install later may pull incompatible pandas, LightGBM or OR-Tools versions. Tested only on Python 3.14 with pandas 3.
- **Route logic assumes every post is exactly 2 hops from a depot.** A deeper network would give wrong deadlines without any error.

**Dead code and leftovers:**
- `world.MODES` is unused.
- The favicon is the default Vite logo.
- `docs/PLAN.md` is stale.
- One TROUBLESHOOTING row about the guided-demo card position is out of date.

**Numbers that can confuse across screens** (none are calculation errors):
- **Foxtrot helicopter sorties:** Point of no return says **33** (the whole shortfall by air); Plan and Drones say **30** (after mules and porters).
- **Alpha helicopter sorties:** Point of no return says **77** if air-only; the plan sends **0** because the jeep goes first.
- **"Lasts (80%)" on the Dashboard** shows the *median* days in large type. The 80% band is the small range next to it. The Posts page labels the same thing "Lasts (80% band)".
- **"4 Oct 2026"** is fixed text in the Plan page chip and the README. It matches the cache today, but will not update.

All numbers in `DEMO_SCRIPT.md` were checked against fresh calculations and **match**:
- 29 Oct, 220×, 19 drone sorties on 26 Oct, 12×;
- Node Mike, 30 → 0, ₹1.67 crore;
- Echo joins, 30 → 49, 27,470 kg.

---

## 5. Honesty check: where the UI or docs claim more than the code does

| Claim | Where | Reality |
|---|---|---|
| "learned from real closure dates and 31 real winters" (about Alpha's date) | Pnr page header, guided demo moment 2, demo script | Only the axes (Zoji La, Manali–Leh) are fitted to real dates. Alpha's and Foxtrot's dates use PLACEHOLDER scaling of the Manali–Leh rule; only the weather replayed is real. |
| "Kerosene is within 9 percent versus 39 percent for a simple average" | EXPLAIN_SIMPLY Q4, Posts page | True on simulated data generated by the same formula the model learns. Says nothing about real use. The on-screen caveat says "simulated", but not that the test is circular. |
| "The yellow Say box … computed from the live data, so the numbers on screen always match" | DEMO_SCRIPT | Moments 1 (title), 3, 6 and 7 contain fixed text. |
| "demo data mein … ek bhi galat alarm nahi aaya" / "Isse galat alarm nahi aate" | EXPLAIN_SIMPLY §8 | True for seed 42 (and 7). Each of 3 other seeds gave 1 false alarm. |
| "The planner solves this week in seconds; a bigger sector adds seconds, not hours" | EXPLAIN_SIMPLY Q21 | Not tested. With 8 posts and troops ×1.5 it already hit the 20-second cap and returned a non-optimal plan. |
| "Weather, terrain and roads are real" | Guided demo moment 6, `/api/health` note | Only the national highways are real roads; every forward road and track is fictional. |
| "Live: today, with the real 16-day forecast" | Top bar tooltip, README | Real only if refreshed with internet; the cache covers 5–20 Oct 2026. Military data and the road bulletin stay at 25 Oct. |
| "Add a new stream … no code changes" | Sources page, EXPLAIN_SIMPLY | Only for data that fits the 7 existing tables and their required columns. |
| "answers the question behind the Army's 2,715-drone RFI: where to put them" | Guided demo moment 4 | It answers it for one fictional week, one fictional geometry and placeholder battery and cost figures. |
| Drone payload "Army RFP (Tribune, Oct 2022)" | Drones chip, FACTS | Matches FACTS (the 363-drone RFP: 15 kg high, 20 kg medium). The team brief said "Tribune 2023"; FACTS correctly says Oct 2022. |

---

## 6. Experiments: different inputs, before vs after

Method: two temporary copies of the project outside the repo (A: original seed 42; B: regenerated with other seeds, or with the anomalies removed). Each test ran in a fresh process. The copy database was restored between tests, and both copies were deleted at the end.

| # | Change | Before (seed 42) | After | Conclusion |
|---|---|---|---|---|
| 1 | **Random seed 42 → 7** (all simulated data rebuilt) | At risk: Alpha, Delta, Foxtrot. Plan ₹1.842 cr, 30 heli, 19 drone sorties. Kerosene error 9.0% (model) vs 39.3% (average) | At risk: **+ Hotel** (winter clothing). Plan ₹1.843 cr, 30 heli, **24** drone sorties, **83 kg not moved**. Kerosene 9.3% vs 38.9%. Closure dates **identical** (same real weather) | Real. **Selfcheck fails on this data.** |
| 2 | **Troops × 1.5 at all posts** | Alpha kerosene shortfall 50,114 L. 3 posts at risk. 30 heli. 0 kg not moved. ₹1.84 cr. OPTIMAL | Shortfall **75,804 L**. **6 posts** at risk. **49** heli (hour cap). **54,539 kg not moved**. ₹2.22 cr. **FEASIBLE** (20-second cap) | Sensible. Planner at its time limit. |
| 3a | **Every closure 10 days earlier** | Alpha last road day 29 Oct (urgent). Foxtrot 25 Oct. Manali–Leh 2 / 13 / 24 Nov | Alpha **passed**. Foxtrot **passed**. **Echo** joins. Heli 30 → **49**. **27,470 kg** not moved. Manali–Leh 25 Oct / 3 / 14 Nov | Sensible |
| 3b | **Every closure 10 days later** | (same) | Alpha **watch** (8 Nov). Foxtrot watch (4 Nov). Only Delta at risk. **0** heli. Cost **₹29,512** | Sensible |
| 3c | **Real weather changed:** sector 4 °C colder in all 31 winters | Alpha 29 Oct; closure 20th percentile 3 Nov | Alpha **26 Oct**, 20th percentile **28 Oct**. Foxtrot **passed**. **Echo** joins. Highway axes unchanged (they use their own pass weather) | **Closure really comes from the weather data** |
| 3d | Sector snowfall × 2 | (same) | Alpha **28 Oct**. Foxtrot 20th percentile **28 Oct**. Echo joins | Sensible |
| 4 | **Fewer drones** (advisor N = 20 / 5 / 1) | — | Best base Node Mike each time. Foxtrot heli 30 → **0 / 20 / 28**. Saved **₹1.67 cr / ₹55.8 lakh / ₹11.1 lakh** | Sensible. Headline text stays hardcoded ("1 drones … only drones are at Roadhead Lima, 19 km away") |
| 4b | **No drones at all** | Delta medicine: 19 drone sorties, ₹29,512 | Delta medicine by **1 helicopter sortie to Post Hotel + porters**. Heli 30 → 31. Plan +₹7.2 lakh | Sensible |
| 4c | Low drone band (up to 6,000 ft) | — | "Save nothing this week": the terrain is too high | Correct |
| 5 | **LightGBM vs weather:** next weeks 8 °C colder | Alpha kerosene, next 30 days (P50): 7,942 L. Cover 4 days. Alpha rations 2,391 kg | Kerosene **9,400 L (+18%)**. Cover **3 days**. Rations **2,391 kg (unchanged)** | **Model really trained and used, for kerosene only.** The average ignores weather. |
| 6a | **OR-Tools:** helicopter hours halved | 30 heli. 11 porter trips. 0 kg not moved. ₹1.84 cr | **14** heli. Porters at max (15). **6,277 kg** not moved. ₹88 lakh | **Really re-optimises.** The 11 porters in the base plan is the exact minimum that lets 30 sorties suffice: solver behaviour, not a script. |
| 6b | Helicopter hours = 0 | (same) | 0 heli. **11,849 kg** not moved. ₹4.3 lakh | Sensible |
| 7 | **Alerts:** injected anomalies removed | 4 alerts | **1** (silent sensor only) | Detection is real, not hardcoded |
| 7b | Alerts on **seeds 1, 2, 3** | 4 alerts, no false alarms | **5 each**: the 4 expected **+ 1 false alarm** (Delta winter clothing; Delta medical twice) | "No false alarms" holds only for the demo seed |
| 8 | Built-in what-ifs | — | Pass early: Echo, 30 → 49, 27,470 kg. Blizzard: 30 → 20, 3,889 kg not moved (cost lower, flagged "not a saving"). Troops +20%: 3 → 5 posts. +20 drones: heli 30 → 0, drone 19 → **809** sorties, ₹1.84 cr → ₹17 lakh | Match the demo script |
| 9 | **Real-weather spot check** | Cached Leh, 20–24 Oct 2021 | Live Open-Meteo API, same dates: **identical values** | Weather cache is genuine |

---

## Top 10 findings by severity

| # | Severity | Finding |
|---|---|---|
| 1 | High | **Forecast accuracy is circular.** The data was generated from the very formula the model learns, so "9% vs 39%" is not evidence of real-world skill. |
| 2 | High | **The scenario is planted.** The 3 short items are set in `gen_data.py`; Delta's closure is a typed bulletin line; Node Mike sits 8.9 km from Foxtrot by design; the selfcheck locks this story in. |
| 3 | High | **Forward-track deadlines are not learned from real closures.** They are PLACEHOLDER scalings of the Manali–Leh rule, but the UI and script say "learned from real closure dates". |
| 4 | High | **Fixed presenter text presented as computed.** Moments 1, 3, 6 and 7; the Foxtrot-only drone headline with the "19 km" sentence; "Track closed by snow"; "15 kg each". |
| 5 | Med–High | **The ₹1.67 crore drone saving rests on placeholders.** Drone cost, batteries and flying hours, 809 sorties a week from one node, and an unchecked supply of that node. |
| 6 | Medium | **Alerts were tuned to the demo seed.** Each of 3 other seeds gave 1 false alarm; the "no false alarms" claim is too strong. |
| 7 | Medium | **The closure fit rests on 4–5 dates per pass**, mostly Low-confidence for Manali–Leh; the High-confidence 8 Dec 2025 date was not used. |
| 8 | Medium | **Live-demo fragility.** "Sync all now" on demo screen 6 clears all caches; Live switch 30–60 s; new drone inputs ~1 min; non-optimal plans are not flagged; requirements are unpinned. |
| 9 | Medium | **Live mode mixes 25-Oct data with today's clock.** Health and sensor hours use the demo clock; the "real forecast" silently goes stale after 20 Oct. |
| 10 | Low–Med | **Planner realism gaps.** Restricted tracks are ignored; capacity is simplified; "bigger sectors add seconds" is untested and contradicted by the 20-second cap at troops ×1.5. |

Minor: Vite favicon; unused `world.MODES`; stale `docs/PLAN.md`; "Lasts (80%)" shows the median; 33-vs-30 and 77-vs-0 helicopter counts across screens need a one-line explanation if the jury asks.
