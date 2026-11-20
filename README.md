# RASAD (रसद)
### Predictive Logistics & Forward Supply Chain System
*Smart India Hackathon 2026 · Problem Statement SIH26251 · Ministry of Defence (Indian Army)*

## What RASAD does

RASAD (रसद, meaning *supplies* in Hindi) is a decision-support prototype for the Indian Army's forward supply chain. It predicts which high-altitude posts are at risk of running critically low on essential supplies (kerosene, rations, medical) **before** the mountain passes close for winter, and recommends the most cost-effective mixed-fleet dispatch plan (truck, jeep, mule, porter, helicopter, drone).

The system runs **fully offline on a laptop**. No internet required during the demo or jury.

## Problem statement

**SIH26251 · Ministry of Defence**
> Develop a predictive logistics system for the Indian Army's forward supply chain that can forecast supply requirements for remote high-altitude posts and optimise dispatch plans across mixed transport fleets, accounting for seasonal pass closures and terrain constraints.

## What it does

| Feature | Description |
|---|---|
| **Supply Forecast** | Post-level demand forecast with 80% confidence band, driven by real weather data |
| **Point of No Return** | Last safe date for road dispatch before winter pass closure, per post and per commodity |
| **Mixed-Fleet Planner** | Optimised dispatch plan across truck / jeep / mule / porter / helicopter / drone |
| **Approve / Modify / Reject** | Role-based workflow for Commander, Logistics Officer, Post QM |
| **Drone Advisor** | Recommends drone deployment at relay nodes to cut helicopter sorties |
| **What-If Scenarios** | 4 live scenarios: early closure, demand spike, fleet reduction, drone scale-up |
| **Anomaly Alerts** | Auto-flags posts where consumption deviates from forecast |
| **Audit Log** | Full decision trail: who approved what, and when |
| **Guided Demo** | 7 moments (`?demo=N`) that walk a jury through the full story |
| **Sources Page** | 10 cited sources with real vs. simulated labels |

## The demo scenario

- **Date:** 25 October 2026 (fictional)
- **Sector:** Sector X (fictional)
- **Posts:** Alpha, Bravo, Charlie, Delta, Echo, Foxtrot, Golf, Hotel

**3 posts at risk:**
- **Alpha.** Kerosene critical. Last road dispatch: 29 Oct. Air cost ~220× road cost.
- **Delta.** Medical low. Requires 19 drone sorties.
- **Foxtrot.** Rations. Drone advisor recommends 20 drones at Node Mike → cuts helicopter sorties from 30 to 0 → saves ~₹1.67 crore.

Demo roles: **Commander / Logistics Officer / Post QM** (no real login required)

## Data sources: real against simulated

**Real data (publicly sourced):**
- Weather: [Open-Meteo](https://open-meteo.com/), 31 winters of historical data
- Terrain: [Copernicus DEM](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model), elevation and slope
- Roads & passes: [OpenStreetMap](https://www.openstreetmap.org/), road network and pass locations
- Pass closure dates: Real historical closure records

**Simulated (not real Army data):**
- Stock levels, consumption rates, troop strength, post locations
- All military operational data
- Cost figures are illustrative placeholders (sourced from public press; not official MoD figures)

> The forecasting engine genuinely calculates from inputs. The demo scenario is deliberately staged to tell a clear story, but the engine underneath is real. Changing any input in the what-if scenarios produces live recalculations.

## Running it

**Requirements:** Python 3.14, Windows

```bash
# 1. Clone the repo
git clone https://github.com/AtulSharmx/RASAD.git
cd RASAD

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
start.bat
# Opens at http://localhost:8000

# 4. Before a jury demo, reset demo data
reset_demo.bat
```

All library versions are pinned. No internet connection needed once dependencies are installed.

## Built with

- **Backend:** Python (Flask)
- **Frontend:** HTML / CSS / JavaScript
- **Data:** Open-Meteo API (cached), Copernicus DEM, OSM
- **Maps:** Toposheet-style strip-bay dashboard

## Folder structure

```
RASAD/
├── backend/        # Flask app, forecast engine, fleet optimizer
├── frontend/       # Dashboard UI, map, scenario panels
├── data/           # Cached weather, terrain, road data
├── docs/           # Design docs, architecture notes
├── ppt/            # SIH presentation slides
├── screenshots/    # UI screenshots
├── sources/        # Source citations and data provenance
├── start.bat       # Launch script (Windows)
└── reset_demo.bat  # Resets demo state before jury
```

## Team: Code Z Crew

| Name | Role |
|---|---|
| **Ishan** | Frontend Developer |
| **Atul Sharma** | Backend & Database |
| **Jatin** | Backend & Database |

*SGT University, Gurugram · BCA (Data Science) · 2026*

## Disclaimer

RASAD is a **prototype built for Smart India Hackathon 2026**. It uses simulated military data and is not connected to any real Indian Army systems. All cost figures and operational scenarios are illustrative only. This project is not affiliated with or endorsed by the Ministry of Defence or the Indian Army.

## How this was built

Three of us built RASAD in two days for SIH 2026. I worked on the backend: the
forecast engine, the fleet optimiser and the data pipeline.

The code was written with AI assistance, using Claude Code. What that did not do is
decide what the thing should calculate, find the public weather and terrain data, or
work out that the point of no return was the number a commander would actually act on.
Every scenario in here was walked through by hand before we put it in front of anyone.
