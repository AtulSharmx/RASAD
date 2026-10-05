# BUILD PROMPT — RASAD (SIH 2026, SIH26251)

Read this whole file before doing anything. Keep it in the project folder and re-read it whenever you lose context.

## 0. Who we are and how to work with us

- Project: **RASAD** (रसद = military supplies). Name can change later.
- Smart India Hackathon 2026, problem statement **SIH26251 — Indian Army: Predictive Logistics & Forward Supply Chain** (Ministry of Defence).
- Team: Ishan, Atul, Jatin. I am Atul. **Nobody in the team can code.** You write and run everything. Explain things to me in very simple, plain language (Hinglish is fine). Never assume I know technical words.
- **Time: 7 days total, and my Claude Pro plan ends next week.** Usage is limited, so be efficient:
  - Plan once, then build. No repeated full audits.
  - After every step, update `PROGRESS.md` (what is done, what is next, how to run it), so a fresh session can continue if this one runs out.
  - Commit to git after every step.
- Ask me whenever you need a decision, a login or something installed. Tell me exactly what to click or type.
- Free tools only. No paid APIs. **No cloud deployment** (no Firebase, Vercel, etc.). Everything runs on my laptop.

## 1. The problem (what MoD actually asked for)

Problem statement, summarised: it is hard to keep assured, timely logistics support to forward formations in dispersed, difficult areas. Demand forecasts, inventory levels, transport capacity, terrain/weather and consumption patterns sit in **multiple separate information streams**, so it is hard to anticipate requirements and optimise the movement of critical supplies.

Technology the PS names: **AI/ML demand forecasting, GIS-enabled logistics planning, IoT-based inventory tracking, and an integrated predictive logistics management system.**

Real-world context (verify and source these in Step 0):
- **Advance Winter Stocking (AWS):** before winter, roughly two lakh tonnes of food, fuel and stores are stocked for Ladakh to last about 6 months, because Zojila and the Manali–Leh passes close. After closure, supply depends on IAF aircraft and helicopters, which are weather-limited and very expensive.
- The last mile to many posts is a jeep track or mule track. Delivery today is by truck, helicopter, mules, porters and air-drops.
- **August 2026: MoD issued an RFI for 2,715 logistics drones** in three altitude bands (up to 6,000 ft, 6,000–12,000 ft, 12,000–20,000 ft). The Army has also deferred disbanding its mule (Animal Transport) units. So the future last mile is a **mixed fleet**: truck + helicopter + mule + porter + drone.
- A tri-service integrated logistics primer notes that the Army (CICG), Navy (ILMS) and Air Force (IMMOLS) inventory systems have no cross-visibility. It recommends API-based interoperability **without disrupting existing systems**, plus QR/RFID traceability.

## 2. What already exists — DO NOT just rebuild this

Other SIH teams have public GitHub projects for this exact PS:
- amrut4469-blip/army-predictive-logistics(-sih): ML demand forecasting (Prophet/XGBoost/LSTM), OR-Tools truck routing, stock-out risk, what-if simulator, offline-first, commander approval.
- Mistique707/forward-logistics: built around Advance Winter Stocking and Zojila closure, LightGBM vs naive baseline, road vs helicopter cost comparison.
- ahmed-ab001/Indian-Army: bases, inventory, convoys, predictive alerts.

So "forecast + routing + map dashboard + what-if" alone is NOT enough. Our base must exist, but our **pitch and polish go into the USPs in section 4**.

## 3. Hard rules (security and honesty)

1. **No real military information.** Never use real post locations, real unit names, real stock numbers or anything classified.
   - Only public towns/places may be used as rear nodes (for example Leh, Kargil, Drass) and public passes/roads.
   - Every forward post is **fictional** ("Post Alpha", "Post Bravo", …) with plausible altitudes.
   - Label the sector "Sector X (fictional)".
2. **Do not invent official numbers.** Consumption scales, payloads, costs and capacities that are not from a public source must be clearly marked `PLACEHOLDER` in code, data and UI, and listed in `docs/PLACEHOLDERS.md`.
3. **Avoid ammunition specifics.** Use supply classes: rations, fuel/kerosene, medical, batteries/spares, winter clothing. If a class needs ammunition, call it "Class V (generic, placeholder)" with no real detail.
4. **On-prem by design.** The whole system runs offline on one machine (in reality: the Army's own network). The only internet use is a one-time weather data download, which is cached. Mention this in the UI ("Runs fully on-premise").
5. Every simulated input is labelled "Simulated for prototype".

## 4. What we will build

### BASE (needed, keep it solid but simple)
1. **Common Logistics Picture (map dashboard):** depots, logistics nodes, fictional posts, roads, passes, mule tracks, helipads and drone legs, with each post's stock status.
2. **Demand forecast per post per supply class** with a confidence band, and **"days of cover left"**.
   - Model: LightGBM (or a simpler model if better), using troop strength, temperature, altitude, day of year and past consumption.
   - Show honest accuracy against a naive baseline on a held-out period, in plain words.
3. **Commander in the loop:** every recommendation can be Approved / Modified / Rejected, and everything is written to an audit log.

### USP A — Mixed-fleet last-mile planner (main USP)
For each day's needs, decide **which mode carries which load**: truck, helicopter, mule/porter or drone.
- Constraints:
  - payload and range limits per mode
  - drone payload dropping with altitude band
  - weather windows (wind, snow, visibility)
  - pass/road status
  - cost (helicopter flying hours)
  - priority (medical and urgent first)
- Use Google OR-Tools.
- Show the plan in a clear table + map, with a one-line plain reason for each choice. For example: "Medicines to Post Delta by drone: 8 kg, urgent, track closed by snow; helicopter would cost ~40×."

### USP B — "Point of No Return" deadline
- Do not treat pass closure as a fixed date. Estimate a **closure date window with probability**, from historical closure dates (Step 0 research) plus current/forecast weather.
- For every post and supply class, compute the **last safe dispatch date by road**, and what happens after it (helicopter hours, cost multiple, risk).
- Headline example: "Post Alpha kerosene: last safe truck dispatch 18 Oct (80% confidence). After that: air maintenance, ~40× cost."

### USP C — Drone deployment advisor (ties to the 2,715-drone RFI)
- "If N drones of altitude class X arrive, where should they be based?"
- Rank posts/nodes by the helicopter hours, porter/mule trips and stock-out risk the drones would save. Show the saving.
- This answers a question MoD is facing right now.

### USP D — Integration adapters (the "multiple information streams" part)
A **source adapter** layer, so new sources plug in without changing the app or existing systems:
- Inventory feed (simulated CICG-like CSV/JSON)
- Weather (real Open-Meteo historical data, cached)
- Road/pass status (simulated BRO-style feed)
- Airlift schedule (simulated IAF feed)
- Post stock updates (from the QM page)

Add a **Sources page** with: health, last sync, record count, and "add a new source = add one config file" (show the file).

### USP E — What-if scenarios
One-click scenarios that re-run the forecast and plan, and show **before vs after**:
- "Pass closes 10 days early"
- "Blizzard grounds helicopters for 3 days"
- "Troop strength +20% at Posts Alpha–Charlie"
- "20 high-altitude drones arrive"

### SHOULD (only if time is left, in this order)
6. **Consumption anomaly alerts:** flag unusual consumption (data error / pilferage / genuine surge) with a simple explanation.
7. **QM stock-update page:** a mobile-friendly web page where a post's quartermaster updates stock by scanning a QR code with the phone camera. No native app.

### WON'T (do not build)
- Native Android app / APK, real IoT hardware, cloud hosting, login with real identities, ammunition details, real locations.

## 5. Tech stack (all free, all local)
- Backend: Python 3.11+, FastAPI, pandas, LightGBM (or statsmodels), Google OR-Tools, SQLite.
- Frontend: React + Vite + TypeScript, Leaflet for maps.
  - Maps: online OSM tiles are OK for the prototype, but bundle a simple GeoJSON basemap of the sector so the map still works fully offline.
  - Note in the docs that production would use an on-prem tile server.
- One-click start for me: `start.bat` (Windows) that starts the backend and frontend and opens the browser. Also `reset_demo.bat` to regenerate the demo data.
- Simple roles for the demo: Commander / Logistics Officer / Post QM (demo login, no real auth). Audit log for every approval and change.

## 6. Step 0 — Research first (before any code)
Use web search. Save the findings in `docs/FACTS.md` with a source URL and a confidence level for every fact:
1. Historical closing and opening dates of Zojila and the Manali–Leh passes (Baralacha La, Tanglang La), for as many recent years as you can find, and the effect of the Atal Tunnel.
2. Open-Meteo historical weather availability for Leh, Kargil and Drass (which variables, and from which year).
3. Logistics drone specs from public RFIs/RFPs and Indian products (altitude bands, payload, range).
4. Public facts on Advance Winter Stocking, air maintenance and last-mile modes.
5. Public helicopter payload-at-altitude and cost figures. If none are reliable, use placeholders.
6. Anything you find in the competitor repos above that we must not duplicate.

Then give me a short **plan**: folder structure, data model, screens, the demo story and the build order. **Wait for my OK.**

## 7. Demo story (design the data around it)
- Simulated date: around late October, just before closure, in "Sector X (fictional)".
- The 3-minute demo must hit these moments in order:
  1. Dashboard: "3 posts at risk".
  2. The Point-of-No-Return alert.
  3. The mixed-fleet plan with reasons and cost.
  4. The drone advisor with savings.
  5. A what-if: "pass closes 10 days early" → before/after.
  6. Sources page: how new data streams plug in.
  7. Commander approves → audit log.

## 8. Build order
1. Step 0 research + plan (wait for OK).
2. Project setup, synthetic data generator (fixed seed), adapters, database, start scripts.
3. Forecasting + days of cover + accuracy check.
4. Point of No Return (USP B).
5. Mixed-fleet planner (USP A).
6. Drone advisor (USP C) + what-if scenarios (USP E).
7. Dashboard UI and all screens, with the design skills.
8. Sources page (USP D), audit log, commander approval.
9. SHOULD items, if time.
10. Polish, a short self-check, screenshots, docs.

If time runs short, steps 3–6 matter most.

## 9. UI / UX
- Use the installed design skills (impeccable, ui-ux-pro-max, frontend-design, web-design-guidelines, Emil Kowalski's skill, make-interfaces-feel-better). Read each skill's instructions first.
- Primary screen size: laptop 1366×768. It must look like a serious operations tool: clear, dense, calm.
  - NOT clichés: no camouflage textures, no fake "hacker green" terminal look, no glowing radar effects.
- Every number has a unit. Every recommendation has a plain-language "why" and a confidence level.
- Hindi labels are optional. English first is fine for this audience.

## 10. Docs and deliverables
- `README.md`: how to start (one click), demo logins, and the honest list of what is simulated.
- `docs/EXPLAIN_SIMPLY.md`: how every part works, in simple Hinglish, so a non-coder can answer jury questions. Include likely jury questions with short answers (data security, why on-prem, model accuracy, what is simulated, how it connects to existing Army systems).
- `docs/DEMO_SCRIPT.md`: 3 minutes, with timings and what to say.
- `docs/PLACEHOLDERS.md` and `docs/FACTS.md`.
- `/screenshots`: clean screenshots of every key screen for the PPT.
- `PROGRESS.md`: kept up to date after every step.
