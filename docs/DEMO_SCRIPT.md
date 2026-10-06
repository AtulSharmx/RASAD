# Demo script

The script follows the **Guided demo** in the app exactly: same 7 moments, same order. The yellow "Say" box in the app shows the line to speak, computed from the live data, so the numbers on screen always match what you say. The lines below are those same lines, shortened for rehearsal.

## Before the demo (10 minutes before)

1. Close any open RASAD window. Double-click **`reset_demo.bat`** (under a minute), then **`start.bat`**.
2. Wait about 1 minute for the first screens to fill in. The internet is not needed.
3. In the browser: zoom at 100% (**Ctrl + 0**), full screen (**F11**). Check the top bar shows **Demo** and the role **Commander**.
4. Open **Guided demo** once, press **Esc** to close it. This warms every screen.
5. If anything looks wrong, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Move with **Next / Back** or the **→ / ←** keys. **Esc** closes the demo. If it closes by mistake, open `http://localhost:8000/#/dashboard?demo=N` (N = the moment number) to jump straight back.

## The 3-minute version

| Time | Moment | On screen | Say |
|---|---|---|---|
| 0:00–0:10 | Opening | Dashboard. Press **Guided demo**. | "RASAD gives a forward-sector commander one logistics picture before the passes close. It runs fully on-premise. Military data here is simulated; weather, terrain, roads and pass-closure dates are real." |
| 0:10–0:35 | **1. Three posts at risk** (`?demo=1`) | Strip bay, "3 posts at risk". Point at the three strips and the red numbered rings on the map. | "Three posts will run short before the routes reopen: Delta's medicine, Foxtrot's rations, Alpha's kerosene. RASAD found them by joining stock, IoT fuel sensors, the forecast and road status. Each strip says how long it lasts, with an 80% band, and the last road day." |
| 0:35–1:00 | **2. Point of no return** (`?demo=2`) | Alpha's strip and the closure curve. Point at the red "Last road day" line. | "Alpha's kerosene: the last safe truck and jeep dispatch is 29 October, with 80% confidence, learned from 31 real winters and real closure dates. After that only air, about 220 times the road cost. The inputs are shown and tagged as placeholders." |
| 1:00–1:30 | **3. Mixed-fleet plan** (`?demo=3`) | Delta's drone line. Point at "19 sorties = 4 drones × up to 5 sorties". | "The planner picks the mode for every load, with a reason and a cost. Delta's track is closed by snow, so its medicine goes by drone: 19 sorties on 26 October, 15 kilograms each, about twelve times cheaper than a helicopter. Alpha's kerosene goes by jeep before its deadline." |
| 1:30–1:55 | **4. Drone advisor** (`?demo=4`) | Headline: helicopter 30 → drone 0. | "If 20 high-altitude drones arrive, base them at Node Mike: Foxtrot then needs 0 helicopter sorties instead of 30, saving about 1.67 crore rupees this week. That answers the question behind the Army's 2,715-drone RFI: where to put them." |
| 1:55–2:20 | **5. What-if** (`?demo=5`) | Before/after table, yellow cells. | "One click: if the pass closes ten days early, Echo joins the posts at risk, helicopter sorties rise from 30 to 49, and 27 tonnes cannot move this week. The commander sees the cost of waiting before it happens." |
| 2:20–2:40 | **6. How data plugs in** (`?demo=6`) | Sources table and the config file on the right. | "Ten streams, each a single config file. Weather, terrain and roads are real; inventory, IoT sensors and the BRO and IAF feeds are simulated because military data is classified. A new stream is one new file, with no change to existing Army systems, as the tri-service Joint Primer recommends." |
| 2:40–3:00 | **7. Commander approves** (`?demo=7`) | Press **Approve** on Delta's drone line (highlighted), then **Show audit log**. | "The system recommends; the commander decides. Approve, and the decision, the role and the time go straight into the audit log. A Post QM cannot approve." Close with: "RASAD: decide before the road shuts." |

## The 1-minute version

Use the same Guided demo, but only these moments.

| Time | Moment | Say |
|---|---|---|
| 0:00–0:15 | 1 | "Three posts will run short before the passes close: Delta's medicine, Foxtrot's rations, Alpha's kerosene." |
| 0:15–0:30 | 2 | "Alpha's last safe truck day is 29 October with 80% confidence, from 31 real winters. After that, air at about 220 times the cost." |
| 0:30–0:45 | 3, then 4 (press Next) | "So the planner sends Alpha's kerosene by jeep now, and Delta's medicine by drone because its track is closed. And 20 new drones at Node Mike would cut Foxtrot's helicopter sorties from 30 to 0." |
| 0:45–1:00 | 7 | Press **Approve**. "The commander approves; it is logged. Runs fully on-premise, on simulated military data and real public weather and terrain." |

## If the jury interrupts

Answer, then continue with **Next**. Short answers to the likely questions are in [EXPLAIN_SIMPLY.md](EXPLAIN_SIMPLY.md). Good screens to open on request:
- "How accurate is it?" → **Posts**, any post: the table shows the method used and why, and the text below the chart gives the error on days the model never saw.
- "What is real?" → **Sources**, or hover over any chip.
- "Where do the costs come from?" → **Point of no return**, the yellow PLACEHOLDER chip.
- "What if the internet is down?" → It already is not needed; say so and carry on.
