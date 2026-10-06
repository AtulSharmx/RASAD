# RASAD (रसद): predictive logistics for forward posts

Smart India Hackathon 2026, problem **SIH26251** (Indian Army: Predictive Logistics & Forward Supply Chain).

RASAD shows a commander which forward posts will run short this winter, **the last safe day to send supplies by road** (as a probability, not a fixed date), **which mode should carry each load** (truck, jeep, mule, porter, helicopter or drone), **where new drones should be based**, and what changes in a what-if. Every recommendation can be approved, modified or rejected, and every decision goes to an audit log. **It runs fully on-premise**: one laptop, no cloud.

## Start it (one click)

1. Double-click **`start.bat`**.
2. Your browser opens **http://localhost:8000**. The first screens can take about 40 seconds while results are prepared.
3. Press **Guided demo** (yellow button, top bar) to walk through the 7 demo moments with Next / Back.
4. Keep the black RASAD window open during the demo. Close it to stop RASAD.

**First run on a new laptop** needs internet once, to install Python and web packages. You need Windows 10/11, Python 3.14 (the exact library versions in `requirements.txt` were tested on 3.14.7) and Node.js 18+ (tested on 24). After that RASAD works **with no internet at all**.

**Reset before a demo:** close the RASAD window, double-click **`reset_demo.bat`** (under a minute; it clears approvals and the audit log), then `start.bat` again.

Problems during a demo: see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Demo roles (demo only, no real login)

Pick the role in the top-right box.

| Role | Can do |
|---|---|
| **Commander** | Approve, modify or reject plan lines |
| **Logistics Officer** | Modify plan lines (cannot approve or reject) |
| **Post QM** | View only |

In deployment, the identity would come from the Army's own login (SSO/PKI); the role picker exists only for the demo.

## Demo and Live clocks

- **Demo** (default): the clock is fixed at **25 Oct 2026, 06:00**, just before the winter closures, so the demo story is the same every time.
- **Live**: the clock is today, and the weather outlook is the **real Open-Meteo 16-day forecast** (cached). Military data stays simulated. The first Live view takes 30–60 seconds to compute.

## Screens

| Screen | What it answers |
|---|---|
| Dashboard | Which posts are at risk? Map of real terrain and roads, fictional posts, and one action strip per risk |
| Posts | Per post and supply: stock, use today, how long it lasts (80% band), forecast method and why |
| Point of no return | Last safe road day (80% confidence), closure window, chance of closure by date, cost of air after it. Pass closures use a rule fitted on real dates; forward roads and tracks use PLACEHOLDER scaling of it |
| Plan | Next 7 days: which mode carries which load, with reason, cost, assumptions; Approve / Modify / Reject. If the solver stops at its 20-second limit, the screen says "best plan found within time limit" |
| Drones | If N drones of a height band arrive, which base saves the most |
| What-if | Pass closes 10 days early, blizzard grounds helicopters, troops +20%, 20 drones arrive: before vs after |
| Alerts | Unusual use (possible data error, unexplained excess, possible surge) and IoT sensors that went silent. Tested on simulated data; thresholds need tuning on real data |
| Sources | The 10 data streams, their health, and the one config file behind each. "Sync all now" asks first, because every screen then recalculates (up to a minute) |
| Audit log | Every approval, change and rejection, with who and when |

## What is real, what is simulated, what is a placeholder

**Real (public, free, no account; downloaded once and cached):**
- Weather since 1995 for Leh, Kargil, Drass, Zoji La, Baralacha La, Tanglang La and the sector (Open-Meteo ERA5), and the 16-day forecast for Live mode.
- Terrain heights (Copernicus DEM GLO-90).
- National highway NH-1/NH-3 roads, the three passes, Leh/Kargil/Drass (OpenStreetMap). Forward roads and tracks are fictional.
- Pass closure and reopening dates (news reports, [docs/FACTS.md](docs/FACTS.md)).
- Public facts: drone RFIs (2,715 drones, 15 kg at high altitude, 10 km range), Advance Winter Stocking, mule-unit deferral, helicopter payloads, the Joint Primer for Integrated Logistics ([docs/FACTS.md](docs/FACTS.md)).

**Simulated** (military data is classified; in deployment it would come from CICG and other systems through the adapters):
- All 8 forward posts (Alpha to Hotel), roadheads, cols and Node Mike: **fictional names and locations**, placed inland on real terrain.
- Stock, daily consumption history, troop strength, IoT fuel-sensor readings, the road/track bulletin and the helicopter allotment.
- Demo weather after 4 Oct 2026, copied from Oct 2021 (a real early-snow year).

**PLACEHOLDER** (made-up numbers, tagged in the app and listed in [docs/PLACEHOLDERS.md](docs/PLACEHOLDERS.md)):
- Consumption scales per person, fleet sizes (mules, porters, jeeps, helicopter hours, drones held), vehicle speeds, weather limits for helicopters and drones, drone batteries.
- **Forward road and track closure rules**: no public dates exist, so they reuse the Manali–Leh rule with placeholder scaling. Every post's last road day comes from these.
- **Costs**: truck ₹0.024/kg-km and helicopter ₹5.33 lakh/hour are derived from one 2020 news report (The Week); mule, porter and drone costs are made up. Every cost multiple in the app shows these inputs.

## Safety and honesty rules

- No real post locations, unit names or stock figures; no ammunition details.
- No international boundary lines are shown. Every fictional site is at least 54 km (posts at least 60 km) from any boundary/LoC/LAC and at least 12 km from any military feature mapped in OpenStreetMap ([docs/SAFETY_CHECK.md](docs/SAFETY_CHECK.md)).
- Forecast accuracy is measured on simulated data — real accuracy unknown until real CICG data is connected. The screen says so next to every accuracy number. The simulated use was generated from the same weather inputs the model uses, so the scores are optimistic.
- The demo scenario is designed: the three short items and Delta's closed track are planted in the simulated data. The calculations are real; [docs/VERIFY_REPORT.md](docs/VERIFY_REPORT.md) shows the outputs changing when the inputs change.

## More documents

- [docs/EXPLAIN_SIMPLY.md](docs/EXPLAIN_SIMPLY.md): how everything works, in simple Hinglish, plus jury questions and answers.
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md): the 3-minute and 1-minute scripts.
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): what to do if something breaks.
- [docs/FACTS.md](docs/FACTS.md), [docs/PLACEHOLDERS.md](docs/PLACEHOLDERS.md), [docs/SAFETY_CHECK.md](docs/SAFETY_CHECK.md), [DESIGN.md](DESIGN.md), [PROGRESS.md](PROGRESS.md).

## How it is built

Python (FastAPI, pandas, LightGBM, Google OR-Tools CP-SAT, SQLite) and React + TypeScript + Leaflet, all running on 127.0.0.1. Check that the core logic works with `.venv\Scripts\python -m backend.selfcheck`.

Data credits: weather © Open-Meteo (CC BY 4.0); terrain Copernicus DEM © DLR/Airbus, provided under COPERNICUS by the EU and ESA; roads © OpenStreetMap contributors (ODbL).
