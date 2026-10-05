"""Safety check for the fictional sites (run by hand: python -m backend.safety_check).

1. Distance from every fictional site to the nearest international boundary / LoC / LAC line, using the
   public low-resolution Natural Earth 1:10m boundary lines. The lines are downloaded into memory ONLY for
   this calculation: never saved, never displayed. Rule: every site must be at least 50 km away.
2. Distance to the nearest military feature mapped in OpenStreetMap (military=* or landuse=military).
   Rule: at least 5 km. Only distances are printed, never names or coordinates.
Writes the result to docs/SAFETY_CHECK.md.
"""
import urllib.parse
from datetime import date

import numpy as np

from backend import db, weather

NE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
NE_FILES = ["ne_10m_admin_0_boundary_lines_land.geojson", "ne_10m_admin_0_boundary_lines_disputed_areas.geojson"]
REGION = (30.0, 38.0, 72.0, 82.0)  # lat min/max, lon min/max: only lines near Ladakh matter
MIN_BOUNDARY_KM, MIN_MILITARY_KM = 50, 5


def _xy(lat, lon, lat0):
    """Local flat projection in km (fine for distances of a few hundred km)."""
    return np.asarray(lon) * 111.32 * np.cos(np.radians(lat0)), np.asarray(lat) * 110.57


def _lines(geom) -> list:
    return [geom["coordinates"]] if geom["type"] == "LineString" else geom["coordinates"]


def boundary_segments() -> np.ndarray:
    """All boundary line segments in the region as rows [lat1, lon1, lat2, lon2]."""
    segs = []
    for f in NE_FILES:
        for feat in weather.fetch_json(NE + f)["features"]:
            for line in _lines(feat["geometry"]):
                pts = np.asarray(line)[:, ::-1]  # GeoJSON is lon,lat
                inside = ((pts[:, 0] > REGION[0]) & (pts[:, 0] < REGION[1]) &
                          (pts[:, 1] > REGION[2]) & (pts[:, 1] < REGION[3]))
                if inside.any():
                    segs.append(np.hstack([pts[:-1], pts[1:]]))
    return np.vstack(segs)


def km_to_segments(lat, lon, segs) -> float:
    px, py = _xy(lat, lon, lat)
    ax, ay = _xy(segs[:, 0], segs[:, 1], lat)
    bx, by = _xy(segs[:, 2], segs[:, 3], lat)
    dx, dy = bx - ax, by - ay
    t = np.clip(((px - ax) * dx + (py - ay) * dy) / np.maximum(dx * dx + dy * dy, 1e-12), 0, 1)
    return float(np.min(np.hypot(ax + t * dx - px, ay + t * dy - py)))


def military_points(bbox) -> np.ndarray:
    q = f"""[out:json][timeout:120];
(nwr["military"]({bbox}); nwr["landuse"="military"]({bbox}););
out geom;"""
    els = weather.fetch_json("https://overpass-api.de/api/interpreter",
                             urllib.parse.urlencode({"data": q}).encode())["elements"]
    pts = []
    for e in els:
        if "lat" in e:
            pts.append((e["lat"], e["lon"]))
        for g in e.get("geometry", []):
            pts.append((g["lat"], g["lon"]))
        for m in e.get("members", []):
            pts += [(g["lat"], g["lon"]) for g in m.get("geometry", [])]
    return np.asarray(pts).reshape(-1, 2)


def main() -> None:
    sites = db.query("SELECT id, name, kind, lat, lon FROM nodes WHERE fictional = 1 ORDER BY kind DESC, id")
    sites += db.query("SELECT id, name, 'col' kind, lat, lon FROM passes WHERE fictional = 1")
    segs = boundary_segments()
    lats, lons = [s["lat"] for s in sites], [s["lon"] for s in sites]
    bbox = f"{min(lats) - 0.25},{min(lons) - 0.3},{max(lats) + 0.25},{max(lons) + 0.3}"  # ~25-30 km margin
    mil = military_points(bbox)
    rows, ok = [], True
    for s in sites:
        b = km_to_segments(s["lat"], s["lon"], segs)
        if len(mil):
            x, y = _xy(mil[:, 0], mil[:, 1], s["lat"])
            px, py = _xy(s["lat"], s["lon"], s["lat"])
            m = float(np.min(np.hypot(x - px, y - py)))
        else:
            m = float("inf")
        good = b >= MIN_BOUNDARY_KM and m >= MIN_MILITARY_KM
        ok &= good
        rows.append(f"| {s['name']} ({s['kind']}) | {b:.0f} km | "
                    f"{'none mapped within ~25 km' if m == float('inf') else f'{m:.1f} km'} | {'OK' if good else 'MOVE'} |")
    report = (
        f"# Safety check — fictional sites\n\nRun on {date.today().isoformat()} with `python -m backend.safety_check`.\n\n"
        f"- **Boundary rule:** every fictional site at least {MIN_BOUNDARY_KM} km from any international boundary, "
        "LoC or LAC line. Lines: Natural Earth 1:10m boundary lines (public domain, low resolution, de facto "
        "lines). They were used **only for this calculation**: held in memory, never saved in the project, never shown in the app.\n"
        f"- **Military-location rule:** no fictional site within {MIN_MILITARY_KM} km of a military feature mapped in "
        "OpenStreetMap (`military=*`, `landuse=military`). Only distances are recorded here. OSM does not map most "
        "military sites, so this check is necessary but not sufficient. The team should also confirm by eye that no "
        "name or location resembles a real post.\n\n"
        f"Result: **{'ALL OK' if ok else 'SOME SITES MUST MOVE'}** ({len(segs)} boundary segments, "
        f"{len(mil)} mapped military points within the search box).\n\n"
        "| Site | Nearest boundary/LoC/LAC | Nearest mapped military feature | Result |\n|---|---|---|---|\n"
        + "\n".join(rows) + "\n")
    (db.ROOT / "docs" / "SAFETY_CHECK.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
