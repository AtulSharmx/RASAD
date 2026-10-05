# Safety check — fictional sites

Run on 2026-10-05 with `python -m backend.safety_check`.

- **Boundary rule:** every fictional site at least 50 km from any international boundary, LoC or LAC line. Lines: Natural Earth 1:10m boundary lines (public domain, low resolution, de facto lines). They were used **only for this calculation**: held in memory, never saved in the project, never shown in the app.
- **Military-location rule:** no fictional site within 5 km of a military feature mapped in OpenStreetMap (`military=*`, `landuse=military`). Only distances are recorded here. OSM does not map most military sites, so this check is necessary but not sufficient. The team should also confirm by eye that no name or location resembles a real post.

Result: **ALL OK** (2435 boundary segments, 512 mapped military points within the search box).

| Site | Nearest boundary/LoC/LAC | Nearest mapped military feature | Result |
|---|---|---|---|
| Roadhead Kilo (roadhead) | 90 km | 34.3 km | OK |
| Roadhead Lima (roadhead) | 63 km | 18.7 km | OK |
| Post Alpha (post) | 82 km | 38.0 km | OK |
| Post Bravo (post) | 91 km | 25.8 km | OK |
| Post Charlie (post) | 86 km | 38.3 km | OK |
| Post Delta (post) | 67 km | 24.4 km | OK |
| Post Echo (post) | 60 km | 15.4 km | OK |
| Post Foxtrot (post) | 78 km | 27.0 km | OK |
| Post Golf (post) | 89 km | 34.8 km | OK |
| Post Hotel (post) | 61 km | 21.3 km | OK |
| Node Mike (node) | 76 km | 24.5 km | OK |
| Col Sierra (col) | 97 km | 17.4 km | OK |
| Col Tango (col) | 54 km | 12.7 km | OK |
| Col Uniform (col) | 88 km | 33.6 km | OK |
