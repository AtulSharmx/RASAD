"""Builds the demo world for Sector X (fictional) with a fixed seed.

It writes simulated feeds into data/feeds/ (as if exported by other systems), rebuilds the
database, and loads every feed through the adapters. Real weather comes from Open-Meteo.
Run: python -m backend.gen_data
"""
import json

import numpy as np
import pandas as pd

from backend import adapters, db, realdata, weather, world
from backend.world import LAPSE, REF_ALT

FEEDS = db.ROOT / "data" / "feeds"
P = db.PARAMS
NOW = pd.Timestamp(P["demo"]["now"])
AS_OF = NOW.normalize() - pd.Timedelta(minutes=1)  # nightly CICG export, 24 Oct 23:59
LAST_DAY = NOW.normalize() - pd.Timedelta(days=1)
CODES = {"rations": "RAT", "kerosene": "SKO", "medical": "MED", "batteries_spares": "BAT", "winter_clothing": "WCL"}
NOISE = {"rations": 0.06, "kerosene": 0.10, "medical": 0.35, "batteries_spares": 0.20, "winter_clothing": 0.40}
OUTLOOK_END = pd.Timestamp("2027-06-30")
OUTLOOK_LOCS = ["sector_x", "zojila", "baralacha", "tanglang", "leh"]

# Days of stock held on the demo date. Most posts are already winter-stocked;
# three are deliberately short so the demo has a problem to solve.
COVER_DAYS = {"PA": 225, "PB": 235, "PC": 215, "PD": 220, "PE": 240, "PF": 210, "PG": 250, "PH": 230}
SHORT = {("PA", "kerosene"): 9, ("PD", "medical"): 3, ("PF", "rations"): 12}
SURGE = ("PF", "2026-09-20", 1.2)  # Foxtrot strength +20% from this date
SILENT_SENSOR = ("PH", "2026-10-23T08:00")  # Hotel's sensor stops reporting
# Injected unusual consumption, kept as ground truth for the anomaly alerts.
ANOMALIES = [
    {"post": "PB", "class": "rations", "start": "2026-08-14", "end": "2026-08-14", "factor": 10, "kind": "data entry error"},
    {"post": "PH", "class": "kerosene", "start": "2026-09-10", "end": "2026-09-24", "factor": 1.45, "kind": "possible pilferage"},
    {"post": "PC", "class": "medical", "start": "2026-10-10", "end": "2026-10-16", "factor": 3, "kind": "genuine surge"},
]
SEGMENTS = {  # simulated road bulletin; anything not listed is OPEN
    "NH1-ZOJILA": ("NH-1 Zoji La", "OPEN", "Open. Night movement suspended."),
    "NH3-BARALACHA": ("NH-3 Baralacha La", "OPEN", "Open for all vehicles."),
    "NH3-TANGLANG": ("NH-3 Tanglang La", "OPEN", "Open for all vehicles."),
    "RHK-PA": ("Track Kilo - Alpha (Col Uniform)", "RESTD", "Fresh snow 20 cm at Col Uniform. One-way, chains required."),
    "RHL-PD": ("Mule track Lima - Delta", "CLOSED", "Blocked by fresh snow."),
}


def outlook() -> pd.DataFrame:
    """Weather after the last real day: the same dates from a past winter (labelled simulated)."""
    year = P["demo"]["analog_year"]["v"]
    frames = []
    for loc in OUTLOOK_LOCS:
        real = pd.read_csv(weather.WEATHER_DIR / f"{loc}.csv", parse_dates=["date"]).set_index("date")
        dates = pd.date_range(real.index.max() + pd.Timedelta(days=1), OUTLOOK_END)
        src = real.reindex(dates - pd.DateOffset(years=NOW.year - year))
        src.index = dates
        frames.append(src.assign(location=loc).rename_axis("date").reset_index())
    out = pd.concat(frames)
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def consumption(rng, wx: pd.DataFrame, posts: list[dict]) -> pd.DataFrame:
    days = pd.date_range(P["demo"]["history_start"], LAST_DAY)
    tmean = ((wx["tmax"] + wx["tmin"]) / 2).reindex(days).to_numpy()
    rows = []
    for n in posts:
        post, alt = n["id"], n["alt_m"]
        strength = np.full(len(days), n["troops"], float)
        for start in range(0, len(days), 90):  # unit rotations change strength a little
            strength[start:] = n["troops"] * (1 + rng.uniform(-0.1, 0.1))
        strength[days >= "2026-09-01"] = n["troops"]
        if post == SURGE[0]:
            strength[days < SURGE[1]] = n["troops"] / SURGE[2]
        strength = np.round(strength)
        t = tmean - LAPSE * (alt - REF_ALT)
        for cls, c in P["classes"].items():
            rate = np.full(len(days), c["per_man_day"]["v"])
            if "extra_per_degC_below_10" in c:
                rate = rate + c["extra_per_degC_below_10"]["v"] * np.clip(10 - t, 0, None)
            if "cold_factor_per_degC_below_0" in c:
                rate = rate * (1 + c["cold_factor_per_degC_below_0"]["v"] * np.clip(-t, 0, None))
            if cls == "medical":
                rate = rate * (1 + (alt - REF_ALT) / REF_ALT)  # more medical use higher up
            if cls == "winter_clothing":
                rate = rate * np.where(days.month.isin([10, 11]), 1.5, 1.0)  # issue season
            qty = strength * rate * rng.lognormal(0, NOISE[cls], len(days))
            for a in ANOMALIES:
                if a["post"] == post and a["class"] == cls:
                    qty[(days >= a["start"]) & (days <= a["end"])] *= a["factor"]
            rows.append(pd.DataFrame({"ISSUE_DT": days.strftime("%Y-%m-%d"), "UNIT_LOC_CODE": post,
                                      "ITEM_CAT": CODES[cls], "QTY_ISSUED": qty.round(1),
                                      "AU": c["unit"], "RATION_STR": strength.astype(int)}))
    return pd.concat(rows, ignore_index=True)


def stock(rng, cons: pd.DataFrame) -> pd.DataFrame:
    recent = cons[cons["ISSUE_DT"] > (LAST_DAY - pd.Timedelta(days=28)).strftime("%Y-%m-%d")]
    mean = recent.groupby(["UNIT_LOC_CODE", "ITEM_CAT"])["QTY_ISSUED"].mean()
    rows = []
    for (post, code), m in mean.items():
        cls = next(k for k, v in CODES.items() if v == code)
        days = SHORT.get((post, cls)) or COVER_DAYS[post] * rng.uniform(0.95, 1.05)
        rows.append({"UNIT_LOC_CODE": post, "ITEM_CAT": code, "QTY_HELD": round(m * days, 1),
                     "AU": P["classes"][cls]["unit"], "AS_ON_DT": AS_OF.strftime("%Y-%m-%dT%H:%M")})
    return pd.DataFrame(rows)


def iot(rng, cons: pd.DataFrame, stk: pd.DataFrame) -> list[dict]:
    """Fuel-tank level every 4 h for 14 days, consistent with issues and the CICG stock."""
    ker = cons[cons["ITEM_CAT"] == "SKO"].pivot(index="ISSUE_DT", columns="UNIT_LOC_CODE", values="QTY_ISSUED")
    ker.index = pd.to_datetime(ker.index)
    hours = pd.date_range((NOW - pd.Timedelta(days=14)).normalize(), NOW, freq="h")
    out = []
    for post in ker.columns:
        daily = ker[post].reindex(hours.normalize(), method="ffill").to_numpy() / 24
        used = pd.Series(np.cumsum(daily), index=hours)
        held = stk[(stk.UNIT_LOC_CODE == post) & (stk.ITEM_CAT == "SKO")]["QTY_HELD"].iloc[0]
        level = held + used[NOW.normalize()] - used  # litres in the tank at each hour
        cap = np.ceil(level.max() * 1.25 / 500) * 500
        for ts in hours[(hours.hour % 4 == 0) & (hours < NOW)]:
            silent = post == SILENT_SENSOR[0] and ts > pd.Timestamp(SILENT_SENSOR[1])
            if silent:
                continue
            fuel = level[ts] * (1 + rng.normal(0, 0.003))
            low_batt = post == SILENT_SENSOR[0] and ts > pd.Timestamp(SILENT_SENSOR[1]) - pd.Timedelta(days=2)
            out.append({"sensor_id": f"FTS-{post}-01", "post_code": post, "ts": ts.strftime("%Y-%m-%dT%H:%M"),
                        "fuel_litres": round(fuel, 1), "level_pct": round(100 * fuel / cap, 1),
                        "capacity_litres": cap, "battery_v": round(3.25 if low_batt else 3.65 + rng.normal(0, 0.02), 2)})
    return out


def roads() -> dict:
    segs = []
    ids = list(SEGMENTS) + [l["id"] for l in db.SECTOR["links"] if l["id"] not in SEGMENTS]
    for i, seg in enumerate(ids):
        name, state, remarks = SEGMENTS.get(seg, (seg, "OPEN", "Open."))
        upd = NOW - pd.Timedelta(minutes=30 + 20 * i)
        segs.append({"seg_id": seg, "name": name, "state": state, "remarks": remarks,
                     "updated": upd.strftime("%Y-%m-%dT%H:%M")})
    return {"issued": (NOW - pd.Timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M"), "segments": segs}


def airlift() -> pd.DataFrame:
    rows = [{"SORTIE_DATE": (NOW + pd.Timedelta(days=d)).strftime("%Y-%m-%d"), "SORTIE_ID": f"HX-{d:02d}{h}",
             "AC_TYPE": "Utility helicopter (generic)", "BASE": "LEH",
             "HRS_ALLOTTED": P["fleet"]["heli_hours_per_day"]["v"] / P["fleet"]["helicopters"]["v"], "TASKED_TO": ""}
            for d in range(7) for h in range(P["fleet"]["helicopters"]["v"])]
    return pd.DataFrame(rows)


def write_placeholders() -> None:
    rows = []

    def walk(node, path):
        if isinstance(node, dict):
            if "v" in node and "src" in node:
                if node["src"].startswith("PLACEHOLDER"):
                    note = node["src"].removeprefix("PLACEHOLDER").lstrip(":; ") or "-"
                    rows.append(f"| `{path}` | {json.dumps(node['v'])} | {note} |")
                return
            for k, v in node.items():
                walk(v, f"{path}.{k}" if path else k)

    walk(P, "")
    (db.ROOT / "docs" / "PLACEHOLDERS.md").write_text(
        "# PLACEHOLDERS\n\n"
        "Numbers we could **not** find in a public source. They are made up for the prototype, "
        "marked `PLACEHOLDER` in `data/params.json` and in the UI, and should be replaced with real "
        "figures by the user unit. This file is generated by `backend/gen_data.py`; do not edit it by hand.\n\n"
        "## Parameters\n\n| Parameter | Value | Note |\n|---|---|---|\n" + "\n".join(rows) + "\n\n"
        "## Everything simulated for the prototype\n\n"
        "- All forward posts, roadheads, cols and nodes (names, coordinates, altitudes, troop strength). "
        "Only Leh, Kargil, Drass and the real passes are real places.\n"
        "- Stock levels, daily consumption history and the injected anomalies.\n"
        "- IoT fuel-sensor readings, the road/track status bulletin and the helicopter allotment.\n"
        "- Weather **after the last real day** (copied from a past winter). Weather up to that day is real (Open-Meteo).\n",
        encoding="utf-8")


def main() -> None:
    print("RASAD: building demo data (seed %d)" % P["demo"]["seed"])
    weather.ensure()
    realdata.ensure()
    FEEDS.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(P["demo"]["seed"])
    outlook().to_csv(FEEDS / "met_outlook.csv", index=False)

    # 1) real data first: the simulated world is built on real terrain and weather
    db.init(reset=True)
    first = {c["id"] for c in adapters.configs() if not c.get("simulated", True)} | {"met_outlook"}
    adapters.sync(first)
    with db.connect() as con:  # real Copernicus DEM heights replace the design heights
        for t in ("nodes", "passes"):
            con.execute(f"UPDATE {t} SET alt_m = (SELECT elev_m FROM terrain WHERE terrain.id = {t}.id) "
                        "WHERE id IN (SELECT id FROM terrain)")
    posts = db.query("SELECT * FROM nodes WHERE kind = 'post' ORDER BY id")
    wx = world.weather("sector_x", "demo")
    wx.index = pd.to_datetime(wx.index)

    # 2) simulated military feeds
    cons = consumption(rng, wx, posts)
    cons.to_csv(FEEDS / "cicg_issues.csv", index=False)
    stk = stock(rng, cons)
    stk.to_csv(FEEDS / "cicg_stock.csv", index=False)
    with open(FEEDS / "iot_fuel_sensors.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in iot(rng, cons, stk))
    (FEEDS / "bro_road_status.json").write_text(json.dumps(roads(), indent=1), encoding="utf-8")
    airlift().to_csv(FEEDS / "iaf_airlift.csv", index=False)
    (db.ROOT / "data" / "anomaly_truth.json").write_text(json.dumps(ANOMALIES, indent=1), encoding="utf-8")
    write_placeholders()
    adapters.sync({c["id"] for c in adapters.configs()} - first)
    for s in adapters.status():
        print(f"  {s['health']:>12}  {s['records'] or 0:>7} rows  {s['name']}" + "".join(f"\n{'':16}{n}" for n in s["notes"]))


if __name__ == "__main__":
    main()
