# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary:** an Indian Army Commander and a Logistics Officer of a forward sector in a high-altitude area, in the weeks before the winter passes close. They decide what goes where, by which mode, before the road shuts. A Post Quartermaster (QM) reports stock.
- **Watching:** the Smart India Hackathon 2026 jury (problem SIH26251, Ministry of Defence), who see the tool on a projector during a 3-minute demo. When the two needs conflict, the screen behaves like the real operations tool; the guided Demo mode carries the presentation (confirmed 5 Oct 2026).

## Product Purpose

RASAD (रसद, "military supplies") joins separate data streams (inventory, consumption, IoT sensors, weather, road status, airlift) into one logistics picture for a forward sector. It forecasts demand per post and supply class, estimates when each route closes as a probability window, gives the last safe date to send supplies by road, plans which mode carries which load (truck, jeep, mule, porter, helicopter, drone), advises where new drones should be based, and shows what-ifs. Success: a commander can see in one minute which posts are at risk, why, what to send, how, by when, and at what cost, then approve it with an audit trail.

## Positioning

- Pass closure is a probability window learned from real closure dates and ~30 real winters, not a fixed date.
- Drones are a real transport mode with RFI payload/range limits, battery cycles and real terrain clearance, plus a basing advisor for the 2,715-drone RFI.
- Data streams plug in through one config file each, without changing existing Army systems (as the HQ IDS Joint Primer, Aug 2025, recommends).

## Operating Context

- Runs fully on-premise on one laptop (in deployment: the Army's own network). No cloud. Internet only for one-time real-data downloads, then cached.
- Shown on a projector or big screen. Primary size 1366×768; must also work at 1920×1080.
- Demo clock: 25 Oct 2026, "Sector X (fictional)". A Live mode uses today's date and the real 16-day forecast.
- Roles: Commander, Logistics Officer, Post QM (demo roles, no real login).

## Capabilities and Constraints

- Screens: Dashboard (map-centred), Post detail, Point of No Return, Mixed-fleet plan (Approve / Modify / Reject), Drone advisor, What-if (before/after), Sources, Audit log; a role switcher; a guided Demo mode for the 7 demo moments.
- Backend API exists (FastAPI on 127.0.0.1:8000): `/api/health, sector, stock, sources, forecast, forecast/{post}, pnr, plan, plan/decision, audit, drones, scenarios, costs, weather, live/refresh`.
- Stack: React + Vite + TypeScript, Leaflet; the map must work offline (no tile server; real OSM roads and Copernicus DEM terrain are cached locally).
- Every number has a unit. Every recommendation has a one-line why and a confidence level.
- Data labels: "Real data", "Simulated" and "PLACEHOLDER" must be visible as small chips, with details and source on hover or click.

## Brand Commitments

- Name shown as "RASAD" with "रसद". English only for the interface.
- Serious, calm operations tool. Explicitly not: camouflage, hacker-green terminal, glowing radar, generic AI dashboard.
- Projector-safe: high contrast, large readable numbers and labels; no thin grey text, no low-contrast dark theme.

## Evidence on Hand

- Real: Open-Meteo weather (archive since 1995 and 16-day forecast), Copernicus DEM heights, OpenStreetMap NH-1/NH-3 roads and the passes, real closure dates (`data/closures.json`), and public facts in `docs/FACTS.md`.
- Simulated (military data is classified): posts, stock, consumption, IoT readings, road bulletin, airlift allotment. Fictional posts Alpha–Hotel, placed ≥60 km from any boundary (`docs/SAFETY_CHECK.md`).
- PLACEHOLDER numbers are listed in `docs/PLACEHOLDERS.md`. Costs come from one 2020 news report (The Week) and are tagged.
- No international boundary lines are ever displayed. No real post locations, unit names or ammunition details.

## Product Principles

1. Decide before the road shuts: every screen points toward the next dispatch decision and its deadline.
2. Honest by construction: every figure carries its source tag, unit and confidence; simulated and placeholder values are never dressed as real.
3. The commander stays in the loop: the system recommends, a person approves, and every action is logged.
4. Plug in, don't replace: new data streams join through adapters without disturbing existing systems.

## Accessibility & Inclusion

Projector viewing: high contrast, large type, colour never the only signal (status also as text or shape), keyboard focus visible.
