---
name: RASAD
description: Predictive logistics for forward posts, laid out as an IAF flight-progress strip bay. Light, projector-safe operations tool.
colors:
  bay-board: "#dfe4dd"
  bay-board-deep: "#d2d8d0"
  strip-paper: "#fffef9"
  ink: "#16212b"
  ink-secondary: "#3a4651"
  rule: "#a9b3ab"
  rule-light: "#d3d9d3"
  mode-road: "#a86b00"
  mode-foot: "#00917f"
  mode-heli: "#2d5fc4"
  mode-drone: "#b0428f"
  status-urgent: "#b8232b"
  status-urgent-tint: "#fbe9ea"
  status-watch: "#8a5100"
  status-watch-tint: "#fff1d6"
  status-ok: "#1d6f43"
  status-ok-tint: "#e3f1e8"
  errata-yellow: "#ffe36e"
  demo-yellow: "#ffd24a"
  map-highway: "#8a3a1c"
  map-contour: "#a8673a"
typography:
  cell-number:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.05
  heading:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 700
    lineHeight: 1.1
  body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.38
  label:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "0.8rem"
    fontWeight: 500
    lineHeight: 1.2
  holder-word:
    fontFamily: "Barlow Condensed, Arial Narrow, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
    lineHeight: 1
  devanagari:
    fontFamily: "Noto Sans Devanagari, sans-serif"
    fontSize: "1.15rem"
    fontWeight: 600
rounded:
  chip: "4px"
  strip: "4px"
  control: "7px"
  panel: "6px"
  pill: "999px"
spacing:
  xs: "0.25rem"
  sm: "0.5rem"
  md: "0.8rem"
  lg: "1rem"
components:
  strip:
    backgroundColor: "{colors.strip-paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.strip}"
  holder-road:
    backgroundColor: "{colors.mode-road}"
    textColor: "#ffffff"
    typography: "{typography.holder-word}"
  holder-drone:
    backgroundColor: "{colors.mode-drone}"
    textColor: "#ffffff"
    typography: "{typography.holder-word}"
  button-ink:
    backgroundColor: "{colors.ink}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "0.5rem 0.95rem"
  button-approve:
    backgroundColor: "{colors.status-ok}"
    textColor: "#ffffff"
    rounded: "{rounded.control}"
    padding: "0.3rem 0.65rem"
  button-demo:
    backgroundColor: "{colors.demo-yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
  chip-real:
    backgroundColor: "{colors.ink}"
    textColor: "#ffffff"
    rounded: "{rounded.chip}"
  chip-placeholder:
    backgroundColor: "{colors.errata-yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
---

# Design System: RASAD

## Overview

**Creative North Star: "The Strip Bay"**

RASAD treats every supply movement the way an IAF air-traffic controller treats a flight: as a paper strip in a bay. A strip has fixed cells (who, how long the stock lasts, the last road day) and a coloured holder that names the transport mode. The commander reads the bay from top to bottom, most urgent first, and stamps the strip to approve it. The world is light and calm, because it is shown on projectors and read by officers who want the decision, not decoration.

The dashboard map borrows the toposheet: a pale shaded relief from the real Copernicus DEM, brown 200 m contours, a legend and a scale bar, and red circled numbers that tie each at-risk post to its strip.

**Key Characteristics:**
- Light bay board, paper strips, ink type; no dark command-centre look.
- Mode is always icon + word + colour, never colour alone.
- Every number carries a unit; every recommendation carries a one-line why and a confidence.
- Data provenance shows as small plies: Real (solid ink), Simulated (dashed hatch), PLACEHOLDER (yellow errata slip).

## Colors

### Primary
- **Ink** (#16212b): all text, the top rail, primary buttons, the selected nav item.

### Secondary
- **Mode holders**, fixed order road, foot, heli, drone, validated for colour-blind separation: road ochre #a86b00, foot teal #00917f, helicopter blue #2d5fc4, drone magenta #b0428f. White labels on all four meet at least 3.9:1 at the 1.25rem bold holder size.

### Tertiary
- **Status** (reserved, always with an icon or word): urgent red #b8232b, watch amber #8a5100, ok green #1d6f43, each with a tint for badge grounds.
- **Errata yellow** #ffe36e marks PLACEHOLDER chips and cells that changed in a what-if. **Demo yellow** #ffd24a is the guided-demo button and spotlight.

### Neutral
- **Bay board** #dfe4dd (page), **board deep** #d2d8d0 (nav rail, bottom rail), **strip paper** #fffef9 (strips, panels, tables), rules #a9b3ab and #d3d9d3, secondary ink #3a4651.

### Named Rules
**The Holder Rule.** A transport mode is shown in its holder colour together with its icon and its word (Jeep, Mule, Porter, Heli, Drone). Status colours are never used for modes.

**The Ply Rule.** Provenance is a ply, not a paragraph: Real is solid ink, Simulated is a dashed hatched ply, PLACEHOLDER is a yellow errata slip. Details live in the chip's popover.

## Typography

Barlow Condensed carries every number, cell value, heading and holder word; Barlow carries sentences and labels; Noto Sans Devanagari sets "रसद" in the brand. All numerals are tabular. The root size is 15px, stepping to 17.5px at 1700px wide so the 1920×1080 projector view reads larger.

### Hierarchy
- **Heading** (Barlow Condensed 700, 1.75rem): screen titles; "3 posts at risk" in urgent red.
- **Cell number** (Barlow Condensed 700, 1.5rem): strip values, dates, costs.
- **Body** (Barlow 500, 1rem): reasons, panel text.
- **Label** (Barlow 500, 0.8rem, secondary ink): cell keys such as "Last road day (80%)".

### Named Rules
**The One Family Rule.** One family (Barlow) at every size; the condensed width is the only change of voice.

## Layout

A fixed shell: ink top rail (3.75rem), a nav rail (5.6rem) with icon + word items, the screen, and a bottom rail (2.6rem) with the pass-closure windows, source health and the on-premise chip. The dashboard gives the map the flexible column and the strip bay a fixed 29rem column on the right. Screens use a 0.8rem gap rhythm. Below 1100px wide the map stacks above the bay and two-column panels become one.

## Elevation & Depth

Flat by default. Strips carry one small two-layer shadow (0 1px 0 and 0 2px 6px at low ink opacity) because they are physical objects in the bay. Popovers and the guided-demo card lift with a soft shadow. The demo spotlight dims everything else with a 42% ink veil.

## Shapes

Small radii, matching paper and plastic: chips and strips 4px, panels 6px, controls 7px, pills only for the round status-number badges. Map at-risk markers are red rings with a numbered badge; posts are squares with a white keyline.

## Components

### Buttons
Ink (primary), line (paper with a rule border), approve (green), reject (paper with a red border), demo (yellow). All press to scale 0.96, transition only colour and scale, and show a 3px blue focus ring.

### Chips
Small (0.76rem) provenance chips: Real, Simulated, PLACEHOLDER. Each is a button that opens a popover with the source on hover, focus or click.

### Cards / Containers
There are no generic cards. Content lives in strips (a holder plus fixed cells plus a why line plus actions) or in plain panels on strip paper.

### Navigation
Left rail with icon over word; the current screen is an ink tile. Tabs (posts, what-if scenarios) are paper buttons that turn ink when selected.

### Strip (signature component)
Holder (mode colour, icon, word) | cells (who, lasts with 80% band, last road day with 80%) | why line with chips | optional action row (stamp, Approve, Modify, Reject). The due cell is boxed in urgent red, or filled red when the road is already closed. An approved strip gets a rotated green stamp.

## Do's and Don'ts

### Do:
- **Do** pair every mode colour with its icon and word.
- **Do** show units on every number and "(80%)" on every confidence-bearing date or band.
- **Do** put cost multiples next to their inputs and a PLACEHOLDER chip.
- **Do** keep text in ink tokens; colour carries identity or status, not sentences.

### Don't:
- **Don't** use camouflage, hacker green, glowing radar or a dark command-centre theme.
- **Don't** show international boundary lines on any map.
- **Don't** reuse status colours (red, amber, green) for transport modes or chart series.
- **Don't** add eyebrow labels above headings or decorate with gradients and glass.
