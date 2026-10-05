"""REAL public data: free, no account, no key. Downloaded once, then cached for offline use.

- Open-Meteo 16-day forecast (for Live mode)            -> data/real/forecast.csv
- Copernicus DEM GLO-90 terrain height (via Open-Meteo) -> data/real/dem.csv
- OpenStreetMap roads, passes and towns (Overpass API)  -> data/real/osm_features.json

Run: python -m backend.realdata [forecast|dem|osm]   (no argument = fetch only what is missing)
"""
import json
import sys
import urllib.parse
from datetime import datetime

import numpy as np
import pandas as pd

from backend import db, weather

REAL = db.ROOT / "data" / "real"
FORECAST, DEM, OSM = REAL / "forecast.csv", REAL / "dem.csv", REAL / "osm_features.json"
GRID = {"lat": (33.80, 34.30), "lon": (76.35, 77.25), "step": 0.015}  # around the fictional sector
BBOX = "32.2,74.7,34.8,78.1"  # Srinagar - Leh - Manali


def fetch_forecast() -> None:
    frames = []
    for name, (lat, lon, elev, _) in weather.LOCATIONS.items():
        q = {"latitude": lat, "longitude": lon, "forecast_days": 16, "timezone": "Asia/Kolkata",
             "daily": ",".join(weather.DAILY)}
        if elev is not None:
            q["elevation"] = elev
        d = weather.fetch_json("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(q))["daily"]
        frames.append(pd.DataFrame(d).rename(columns={"time": "date", **weather.DAILY}).assign(location=name))
    pd.concat(frames).dropna(subset=["tmax", "tmin"]).to_csv(FORECAST, index=False)


def _elevations(lats, lons) -> list[float]:
    out = []
    for i in range(0, len(lats), 100):  # the API takes up to 100 points per call
        q = {"latitude": ",".join(f"{x:.4f}" for x in lats[i:i + 100]),
             "longitude": ",".join(f"{x:.4f}" for x in lons[i:i + 100])}
        out += weather.fetch_json("https://api.open-meteo.com/v1/elevation?" + urllib.parse.urlencode(q))["elevation"]
    return out


def fetch_dem() -> None:
    """Height of every node and pass, plus a ~1.5 km grid over the sector (for drone legs and siting).
    Only points not already in the cache are downloaded."""
    pts = [(n["id"], n["lat"], n["lon"]) for n in db.SECTOR["nodes"] + db.SECTOR["passes"]]
    g = GRID
    pts += [("grid", a, b)
            for a in np.arange(g["lat"][0], g["lat"][1] + 1e-9, g["step"])
            for b in np.arange(g["lon"][0], g["lon"][1] + 1e-9, g["step"])]
    want = pd.DataFrame(pts, columns=["id", "lat", "lon"]).round({"lat": 4, "lon": 4})
    key = lambda d: d["id"] + "@" + d["lat"].astype(str) + "," + d["lon"].astype(str)
    have = {}
    if DEM.exists():
        old = pd.read_csv(DEM).round({"lat": 4, "lon": 4})
        have = dict(zip(key(old), old["elev_m"]))
    want["k"] = key(want)
    missing = want[~want["k"].isin(have)]
    if len(missing):
        have.update(zip(missing["k"], _elevations(missing["lat"].tolist(), missing["lon"].tolist())))
    want.assign(elev_m=want["k"].map(have)).drop(columns="k").to_csv(DEM, index=False)


def _thin(coords: list[dict], min_km: float = 0.15) -> list[list[float]]:
    """Drop points closer than ~150 m to the last kept one; keeps the cache small."""
    kept = [coords[0]]
    for c in coords[1:-1]:
        if abs(c["lat"] - kept[-1]["lat"]) + abs(c["lon"] - kept[-1]["lon"]) * 0.83 > min_km / 111:
            kept.append(c)
    kept.append(coords[-1])
    return [[round(c["lat"], 5), round(c["lon"], 5)] for c in kept]


def fetch_osm() -> None:
    q = f"""[out:json][timeout:180];
way["highway"]["ref"~"NH ?(1|3)([^0-9]|$)"]({BBOX});
out geom;
(node["mountain_pass"="yes"]["name"~"Zoji|Baralacha|Bara-lacha|Tanglang|Taglang",i]({BBOX});
 node["place"~"town|city|village"]["name"~"^(Leh|Kargil|Drass|Dras)$"]({BBOX}););
out body;"""
    els = weather.fetch_json("https://overpass-api.de/api/interpreter",
                             urllib.parse.urlencode({"data": q}).encode())["elements"]
    feats = []
    for e in els:
        t = e.get("tags", {})
        if e["type"] == "way":
            geom = _thin(e["geometry"])
            kind = "road"
        else:
            geom = [round(e["lat"], 5), round(e["lon"], 5)]
            kind = "pass" if t.get("mountain_pass") == "yes" else "town"
        feats.append({"id": f"osm/{e['type']}/{e['id']}", "kind": kind, "name": t.get("name:en") or t.get("name", ""),
                      "ref": t.get("ref", ""), "ele": t.get("ele", ""), "geometry": json.dumps(geom)})
    OSM.write_text(json.dumps({"fetched": datetime.now().isoformat(timespec="seconds"),
                               "attribution": "(c) OpenStreetMap contributors, ODbL", "features": feats}),
                   encoding="utf-8")


def dem_matches_sector() -> bool:
    """True if the DEM cache has a height for every node/pass at its current coordinates."""
    if not DEM.exists():
        return False
    have = {(r.id, round(r.lat, 4), round(r.lon, 4)) for r in pd.read_csv(DEM).itertuples()}
    return all((n["id"], round(n["lat"], 4), round(n["lon"], 4)) in have
               for n in db.SECTOR["nodes"] + db.SECTOR["passes"])


def ensure(refresh: tuple = ()) -> None:
    REAL.mkdir(parents=True, exist_ok=True)
    for name, path, fn in [("forecast", FORECAST, fetch_forecast), ("dem", DEM, fetch_dem), ("osm", OSM, fetch_osm)]:
        stale_dem = name == "dem" and not dem_matches_sector()
        if name in refresh or not path.exists() or stale_dem:
            print(f"  downloading real data: {name} ...", flush=True)
            fn()


if __name__ == "__main__":
    ensure(tuple(sys.argv[1:]))
