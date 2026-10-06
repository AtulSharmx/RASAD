# RASAD idea PPT: slide plan

> **Approved on 6 Oct 2026, with these changes (built into `RASAD_SIH26251.pptx`; they override the plan below):**
> 1. Theme = Transportation & Logistics; Category = Software.
> 2. Team Name **Code ZCrew**, Team ID **163616**: on slide 1 and in the ovals on slides 2–6 (`TEAM_NAME` / `TEAM_ID` in `build_deck.py`).
> 3. No member names or college: the template has no field for them.
> 4. Impact slide:
>    - Only 2 headline numbers, each tagged:
>      - "29 Oct", tagged *simulated · PLACEHOLDER track rules*, because it depends on the placeholder track rules, not on costs.
>      - "30 → 0", tagged *simulated · PLACEHOLDER costs*.
>    - Six operational benefits: decide before the passes close; less risk to troops; ready for the 2,715 drones; full accountability; plugs into existing systems; scales to other sectors.
> 5. Slide 2: about 30 words besides the screenshot.
> 6. Feasibility: the honest admissions as a "Limitation → Mitigation" table.

Template: `ppt/template.pptx` (official SIH 2026 format).
- **6 slides.** The instructions slide (slide 7) is deleted.
- **Kept exactly:** slide titles 3–6, every "pointer" heading, the SIH logo, the blue footer and the "Your Team Name" oval (filled with our team name).
- **Visual style:** the template's white background and blue, plus the app's own mode colours (road, foot, helicopter, drone), so the screenshots and diagrams match. Body text 14 pt or larger; Calibri and Arial only, so nothing reflows in the PDF.
- **Every number below comes from:**
  - our app (checked against a fresh run on 6 Oct 2026), or
  - `docs/FACTS.md`, `PLACEHOLDERS.md`, `VERIFY_REPORT.md` or `DEMO_SCRIPT.md`.
- Every demo number carries a small tag: **"Demo scenario · simulated military data · PLACEHOLDER costs"**.

**I need from you before building** (blanks are marked ⬜):
1. Team name.
2. Team ID.
3. The exact **Theme** shown for SIH26251 on sih.gov.in. I could not find it publicly.
4. OK to add "SGT University, Gurugram" and the member names in small text on the title slide? The template does not ask for them; most teams add them.
5. FYI (not a slide question): the SIH 2026 rules we found say teams need **6 members, at least one female** (see `RESEARCH.md`). Please check with your SPOC.

---

## Slide 1 — TITLE PAGE

**Template asks:** Problem Statement ID, Title, Theme, PS Category, Team ID, Team Name.

**Text:**
- Keep the "SMART INDIA HACKATHON 2026" heading.
- Replace "TITLE PAGE" with **RASAD (रसद) — decide before the road shuts**.
- Bullets:
  - Problem Statement ID – **SIH26251**
  - Problem Statement Title – **Indian Army: Predictive Logistics & Forward Supply Chain** (Ministry of Defence)
  - Theme – ⬜
  - PS Category – **Software**
  - Team ID – ⬜
  - Team Name – ⬜
- Small line under the bullets (if you agree): *SGT University, Gurugram · Ishan · Atul · Jatin*

**Visual:** the template's own SIH brain-bulb art, unchanged.

**Why it scores:** clean, complete and correct. A wrong or missing field looks careless before the jury reads anything.

---

## Slide 2 — IDEA TITLE → "RASAD (रसद): decide before the road shuts"

**Template asks:** *Proposed Solution (Describe your Idea/Solution/Prototype)*: detailed explanation; how it addresses the problem; innovation and uniqueness.

**Layout:** left ~55% text, right ~45% dashboard screenshot.

**Text:**
- Heading (kept): ❖ *Proposed Solution (Describe your Idea/Solution/Prototype)*
- Lead line (bold): **A working, offline decision tool: which forward posts will run short this winter, the last safe day to send supplies by road, and which mode should carry each load.**
- *Detailed explanation*, shown as a 4-step arrow flow, one short line each:
  1. **Forecast need**: per post and supply, with an 80% band
  2. **Point of No Return**: last safe road day at 80% confidence, from 31 real winters of weather
  3. **Mixed-fleet plan**: truck · jeep · mule · porter · helicopter · drone, each line with a reason and a cost
  4. **Commander decides**: Approve / Modify / Reject, and every decision goes to the audit log
- *How it addresses the problem:* The problem statement says stock, consumption, transport, terrain and weather sit in separate streams. RASAD joins **10 streams** through adapters into **one picture**: AI/ML forecasting, GIS terrain, IoT fuel sensors and an integrated plan.
- *Innovation and uniqueness*, as 5 short chips:
  - Road closure as a **probability window**, not a fixed date
  - **Drones as a real mode** (15 kg, 10 km, must clear the terrain)
  - **Drone basing advisor**: answers "where?" for the 2,715-drone RFI
  - **Commander approves**, with every decision audited
  - **On-premise, works offline**

**Visual:**
- **Screenshot `01-dashboard`**: real terrain map, 3 numbered posts at risk, action strips.
- Caption: *"Working prototype. Military data simulated; terrain, highways and weather real."*

**Why it scores:**
- **Innovation** carries the most weight in unofficial guides (~25%).
- The jury sees a **working product** on the first content slide; most idea decks show mock-ups.
- It uses the exact words of the problem statement: AI/ML, GIS, IoT, integrated system.

---

## Slide 3 — TECHNICAL APPROACH

**Template asks:** *Technologies to be used*; *Methodology and process for implementation (flow charts / images / working prototype).*

**Layout:** a tech-stack chip row at the top, a full-width data-flow diagram in the middle, and a prototype "proof strip" at the bottom.

**Text, *Technologies to be used*** (chips, grouped):
- **AI/ML:** LightGBM quantile forecast (P10 / P50 / P90), checked against a 28-day average
- **Optimisation:** Google OR-Tools CP-SAT
- **GIS:** Leaflet map, Copernicus DEM GLO-90 terrain, OpenStreetMap
- **Backend:** Python, FastAPI, pandas, SQLite
- **Frontend:** React + TypeScript
- **Hardware:** one laptop or server on the Army's own network; IoT fuel-tank sensors (simulated); **no cloud**

**Diagram, *Methodology and process*:** native shapes, left to right:

- **1. 10 data streams**
  - Real: Open-Meteo ERA5 weather (since 1995), 16-day forecast, Copernicus DEM, OpenStreetMap
  - Simulated (dashed outline): CICG-like stock and issues, IoT fuel sensors, BRO-like road status, IAF-like airlift, weather outlook
- **2. Adapters**
  - One config file per stream
  - Unknown codes refused
  - Health and staleness checks
- **3. One on-premise database** (SQLite)
- **4. Engines**
  - Forecast → Point of No Return (rule fitted to real closure dates, 31 real winters replayed) → Mixed-fleet plan (7 days)
  - Branches: Drone advisor · What-if · Data alerts
- **5. Commander**
  - 9 screens · Approve / Modify / Reject · Audit log

**Prototype proof strip:**
- A crop of the real **Plan** screen line: *"19 drone sorties from Roadhead Lima … leg clears 5,801 m, so 15 kg per sortie … ~₹108/kg; helicopter ~₹1,344/kg (~12×)"*.
- Caption: *"Every plan line explains itself (PLACEHOLDER costs)."*

**Why it scores:**
- It shows **how**, not "we will use AI": named models, the solver, real data sources and the flow.
- Flowcharts are the single most recommended item in the finalist write-ups.

---

## Slide 4 — FEASIBILITY AND VIABILITY

**Template asks:** *Analysis of the feasibility*; *Potential challenges and risks*; *Strategies for overcoming these challenges*.

**Layout:** a left column of 5 check-marked feasibility points; on the right, a 2-column table whose headers are the template's own pointers 2 and 3.

**Text, *Analysis of the feasibility of the idea*:**
- ✔ **Already built and running:** 9 screens, guided demo, one-click start
- ✔ **One laptop, fully offline** after a one-time public-data download; nothing leaves the machine
- ✔ **Free, open-source stack:** no licence or cloud cost
- ✔ **Plugs into existing systems through their exports** (CICG, BRO, IAF) without changing them, as the HQ IDS Joint Primer (Aug 2025) recommends
- ✔ **Tested by changing inputs:**
  - Troops ×1.5 → posts at risk go from 3 to 6.
  - Pass closes 10 days early → helicopter sorties go from 30 to 49.

**Table:**

| Potential challenges and risks | Strategies for overcoming these challenges |
|---|---|
| Military data is classified; ours is simulated | Adapters map real CICG/BRO/IAF exports with one config file each; simulated data is labelled on every screen |
| Forecast accuracy is so far measured only on simulated data | Model is used only where it beats a 28-day average on held-out days; 80% bands; real accuracy will be measured once CICG data is connected |
| Few real closure dates (4–5 per pass; error ±13 / ±18 days) | Plan at 80% confidence, not the middle date; add BRO's own records |
| Forward-track closure rules and all costs are PLACEHOLDER | Tagged on screen; one parameters file for the unit to replace |
| Security and access | On-premise, local only; demo roles today → Army SSO/PKI in deployment |
| Bigger sectors may slow the plan solver | 20-second limit with "best plan found within time limit" shown on screen; to be tested at sector scale |

**Visual:**
- The table, plus small icons: offline, rupee-free, plug, check.
- **Optional:** a thin crop of the Sources screen (10 streams, health).

**Why it scores:**
- It answers all three pointers literally.
- It names real risks with concrete fixes. That honesty builds trust and matches what we will say in a live demo.

---

## Slide 5 — IMPACT AND BENEFITS

**Template asks:** *Potential impact on the target audience*; *Benefits of the solution (social, economic, environmental, etc.)*.

**Layout:** a top row of 4 big stat cards from the working demo (with the honesty tag); below them, two columns for the two pointers.

**Stat cards** (all from `DEMO_SCRIPT.md` / `VERIFY_REPORT.md`):
1. **29 Oct**: Alpha's last safe road day (80% confidence). *Act before it.*
2. **~220×**: air vs road cost per kg after that day (PLACEHOLDER costs)
3. **30 → 0**: Foxtrot's helicopter sorties this week with 20 drones at the advised base, saving **~₹1.67 crore** (PLACEHOLDER costs)
4. **30 → 49**: helicopter sorties if the pass closes 10 days early, with 27 t that cannot move. *The cost of waiting, shown before it happens.*
- Tag: *"Demo scenario · simulated military data · real weather and terrain · PLACEHOLDER costs (docs/PLACEHOLDERS.md)"*

**Text, *Potential impact on the target audience*:**
- **Commanders and logistics staff:** one picture with the deadline and the plan; they decide, and it is logged
- **Post quartermasters:** early warning before stock runs out
- **Air-effort planners:** fewer emergency sorties in bad weather. Only 72% of past winter days were inside the helicopter limits; the limits themselves are placeholders.
- **Drone procurement (2,715-drone RFI):** where to base drones, by altitude band

**Text, *Benefits*:**
- **Economic:** the cheapest safe mode is chosen per load, and the air cost is visible before anyone commits
- **Safety / social:** fewer risky sorties and porter trips in bad weather; plans the real mixed fleet (mule units retained to ~2032)
- **Environmental:** fewer helicopter hours means less aviation fuel (not quantified)
- **Accountability:** every approval is logged with role and time
- **Scale:** the same adapters can serve other sectors and the Navy (ILMS) and IAF (IMMOLS) systems named in the Joint Primer

**Visual:** the 4 stat cards (big numbers, mode icons), plus a small crop of the drone-advisor headline (`05`) if it fits.

**Why it scores:**
- Impact is quantified with numbers the jury can see in the running app, and each is honestly tagged.
- It names real beneficiaries and links to a live MoD procurement (the 2,715-drone RFI).

---

## Slide 6 — RESEARCH AND REFERENCES

**Template asks:** *Details / Links of the reference and research work.*

**Layout:** references in 3 labelled groups (left two-thirds); a "What we verified" panel on the right.

**References** (short title + source + link, from `FACTS.md`):

*Problem and policy*
1. MoD RFI for 2,715 logistic drones in 3 altitude bands (Aug 2026): idrw.org, outlookindia.com
2. Army RFP for 363 logistics drones: 15 kg at high altitude, 10 km range (The Tribune, 17 Oct 2022)
3. Joint Primer for Integrated Logistics, HQ IDS (Aug 2025): via PIB / GlobalSecurity
4. Advance Winter Stocking (~2 lakh t for ~6 months) and cost quotes (The Week, 13 Aug 2020)
5. Mule units retained to ~2032 (SP's Land Forces, 27 Nov 2025)
6. Q-FORCE logistics app (AIR News, 22 May 2026)

*Real closure dates*

7. Zoji La 2020–25: Greater Kashmir, The Tribune, ThePrint, AIR News
8. Manali–Leh 2021–26: AIR News, himalayan-routes, Discover Leh Ladakh

*Open data used (real, cached offline)*

9. Open-Meteo ERA5 archive and forecast (CC BY 4.0)
10. Copernicus DEM GLO-90 (© DLR/Airbus, EU/ESA) · OpenStreetMap (ODbL)
11. Sabal 20 drone specifications (The Defense Post, Dec 2024)

**"What we verified" panel:**
- **Prior work:** 3 public prototypes for this problem statement studied; none plans drones or gives a closure probability.
- **Our own check** (`VERIFY_REPORT.md`): the outputs move correctly when inputs change. Military data is simulated; costs are placeholders.

**Visual:** small group icons (shield, mountain-pass, database) and the clean list.

**Why it scores:**
- Real, checkable links replace "Science Direct".
- It shows depth of research and honesty about what is simulated.

---

## Build steps (after your "yes")

1. **Fill the template.** Copy `template.pptx`, then fill it with python-pptx: text in the existing placeholders, plus native shapes, tables and the screenshots. Delete slide 7. Compress the screenshots to JPEG of about 1,600 px.
2. **Make the PDF.** Export it with **PowerPoint itself**, for exact template fonts. Check it is **under 5 MB**.
3. **QA.**
   - Render every page to an image and check: no overflow, nothing cut off, readable at 100%.
   - Run `markitdown`, check for leftover template text, and run the skill's validator against the template.
4. **Save, commit and push.** Save as `ppt/RASAD_SIH26251.pptx` and `ppt/RASAD_SIH26251.pdf`, then commit and push. The app code is not touched, so the code freeze stays.
