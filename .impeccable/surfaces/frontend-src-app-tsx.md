---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: []
---

# RASAD web app (all screens)

Scope: the whole operations app (Dashboard, Post detail, Point of no return, Plan, Drones, What-if, Sources, Audit log, role switcher, guided Demo mode). Mode: Operate. Audience: Commander / Logistics Officer on a projector; SIH jury watching. Task: see which posts are at risk, why, what to send, by which mode, by when, at what cost; approve with an audit trail.

## Direction contract

THESIS: An IAF flight-progress strip bay for supply movements. Every recommendation is a strip with fixed cells (who, how long it lasts, last road day), its holder naming the mode in icon + word + colour. Refuses the dark command-centre dashboard and the white SaaS card grid.

OWN-WORLD: Light grey-green bay board (#dfe4dd), paper strips (#fffef9) with ink (#16212b), mode holders: road ochre #d39b1f, foot brown #8a5a2b, helicopter blue #1f5fa8, drone violet #5a3fa0; urgent red #b8232b. Barlow Condensed for cells and numbers, Barlow for text. Provenance chips as plies: Real = solid ink, Simulated = dashed hatched ply, PLACEHOLDER = yellow errata slip. Map on the dashboard in toposheet style: subtle brown contours over a pale relief, legend, scale bar, red circled numbers on at-risk posts.

STORY: The commander reads the bay top-down: three posts at risk, each strip saying what runs out, when the road shuts and how it will go. One click opens the reason, cost inputs and the approve stamp.

FIRST VIEWPORT: Ink top rail (RASAD रसद, Sector X fictional, clock, Demo/Live, Guided demo, role). Left nav rail. Map ~60% width, centre. Strip bay 450px right: "3 posts at risk" then three strips, then stocked posts. Bottom rail: pass closure windows, source health, on-premise chip.

FORM: Candidate 3 of the grounded list (ATC flight-progress strip board); seed key d9baba11. Raises: cells flip in place on what-if without reflowing (split-flap); provenance as plies (acetate manual); one family at every size (bitmap specimen). User addition: B's toposheet map on the dashboard.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
