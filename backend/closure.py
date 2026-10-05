"""Step 4 (USP B): Point of No Return.

A pass or track does not close on a fixed date. We fit a simple rule to REAL closure dates (Zoji La and
Manali-Leh / Baralacha La): "it closes on the first day when EITHER this winter's snow so far is at least
C cm and the last 3 days brought at least D cm (heavy snow), OR the 7-day average temperature is at or
below T degC (ice)". Then we replay this season against ~30 past winters of REAL weather: "if the rest of
this winter is like 1995, 1996, ... 2025, when does each route close?". That gives a closure-date
distribution. The last safe dispatch is the date on which the route is still open with 80% probability,
minus transit and loading time.
"""
import functools
import json
import math

import numpy as np
import pandas as pd

from backend import costs, db, forecast, world

CLOSURES = json.loads((db.ROOT / "data" / "closures.json").read_text(encoding="utf-8"))
P, CP = db.PARAMS, db.PARAMS["closure"]
M = P["modes"]
DAY = pd.Timedelta(days=1)
SEASON_DAYS = 213  # 1 Oct to 1 May
C_GRID, D_GRID = np.arange(0, 310, 10), np.arange(0, 64, 4)
T_GRID = np.concatenate([[-99.0], np.arange(-22, -4.5, 0.5)])  # -99 = cold never closes it
WINTERS = range(1995, 2026)  # winters starting in these years (real ERA5 weather)


def _season_start(d: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(year=d.year if d.month >= 10 else d.year - 1, month=10, day=1)


def _real(location: str) -> pd.DataFrame:
    """Real daily snowfall and mean temperature (archive only)."""
    w = world.weather(location, "demo")
    w = w[w["source"] == "open_meteo"]
    return pd.DataFrame({"snow": w["snowfall_cm"].fillna(0).to_numpy(),
                         "t": ((w["tmax"] + w["tmin"]) / 2).to_numpy()}, index=pd.to_datetime(w.index))


def _season(w: pd.DataFrame, year: int) -> np.ndarray:
    """Rows [snow, temp]: 6 days before 1 Oct (for the 7-day average) plus the season."""
    days = pd.date_range(pd.Timestamp(f"{year}-10-01") - 6 * DAY, periods=SEASON_DAYS + 6)
    x = w.reindex(days)
    return np.vstack([x["snow"].fillna(0).to_numpy(), x["t"].interpolate().bfill().ffill().to_numpy()])


def _signals(x: np.ndarray, fresh_from: int = 0) -> tuple:
    """Per season day: snow so far, snow in the last 3 days, 7-day average temperature.
    Storms before `fresh_from` (today) do not count in the 3-day sum: the road status feed already
    tells us whether they closed the route."""
    snow = x[0, 6:]
    fresh = snow.copy()
    fresh[:fresh_from] = 0
    t7 = np.convolve(x[1], np.ones(7) / 7, "valid")
    return np.cumsum(snow), np.convolve(fresh, np.ones(3))[:len(snow)], t7


def _first(ok: np.ndarray, start: int = 0) -> np.ndarray:
    """Index of the first True on or after `start` along the last axis; SEASON_DAYS if none."""
    ok = ok.copy()
    ok[..., :start] = False
    return np.where(ok.any(-1), ok.argmax(-1), SEASON_DAYS)


def _closing_day(x: np.ndarray, c: float, d: float, t: float, start: int = 0) -> int:
    cum, storm, t7 = _signals(x, start)
    return int(_first(((cum >= c) & (storm >= d)) | (t7 <= t), start))


@functools.lru_cache(maxsize=4)
def fit(pass_id: str) -> dict:
    """Best (C, D, T) on the real closure dates, plus a leave-one-winter-out error so we don't fool ourselves."""
    info = CLOSURES[pass_id]
    w = _real(info["weather"])
    obs = []
    for s in info["closed"]:
        d = pd.Timestamp(s)
        obs.append((_season_start(d).year, (d - _season_start(d)).days))
    seasons = {y: _season(w, y) for y, _ in obs}
    table = {}  # closing day for every (C, D, T), per winter
    for y, x in seasons.items():
        cum, storm, t7 = _signals(x)
        by_snow = _first((cum >= C_GRID[:, None, None]) & (storm >= D_GRID[None, :, None]))  # (C, D)
        by_cold = _first(t7 <= T_GRID[:, None])  # (T,)
        table[y] = np.minimum(by_snow[:, :, None], by_cold[None, None, :])

    def best(rows):
        err = sum(np.abs(table[y] - day) for y, day in rows)
        i, j, k = np.unravel_index(np.argmin(err), err.shape)
        return float(C_GRID[i]), float(D_GRID[j]), float(T_GRID[k]), float(err[i, j, k] / len(rows))

    c, d, t, mae = best(obs)
    loo = [abs(_closing_day(seasons[y], *best([o for o in obs if o[0] != y])[:3]) - day) for y, day in obs]
    return {"pass": pass_id, "C_cm": c, "D_cm": d, "T_c": None if t < -90 else t,
            "fit_error_days": round(mae, 1), "loo_error_days": round(float(np.mean(loo)), 1), "years": len(obs),
            "rows": [{"winter": f"{y}-{(y + 1) % 100:02d}",
                      "real": (pd.Timestamp(f"{y}-10-01") + day * DAY).date().isoformat(),
                      "rule": (pd.Timestamp(f"{y}-10-01") + _closing_day(seasons[y], c, d, t) * DAY).date().isoformat()}
                     for y, day in obs]}


def _reopen_day(pass_id: str) -> int:
    """Late-case (80th percentile) reopening, as days after the season's 1 Oct, from real dates."""
    days = [(pd.Timestamp(s) - _season_start(pd.Timestamp(s))).days for s in CLOSURES[pass_id]["reopened"]]
    return int(np.percentile(days, 80))


def _members(location: str, mode: str, snow_scale: float, t_shift: float) -> tuple[int, list]:
    """This season so far (and, in Live mode, the real forecast), followed by each past winter."""
    now = world.clock(mode).normalize()
    start = _season_start(now)
    w = world.weather(location, mode)
    w.index = pd.to_datetime(w.index)
    end = now
    if mode == "live" and (w["source"] == "open_meteo_forecast").any():
        end = w.index[w["source"] == "open_meteo_forecast"].max() + DAY
    w = w[(w.index >= start - 6 * DAY) & (w.index < end)]
    known = np.vstack([w["snowfall_cm"].fillna(0).to_numpy(), ((w["tmax"] + w["tmin"]) / 2).to_numpy()])
    hist = _real(location)
    out = []
    for y in WINTERS:
        x = _season(hist, y)
        x[:, :known.shape[1]] = known
        out.append(np.vstack([x[0] * snow_scale, x[1] + t_shift]))
    return (now - start).days, out


def segment(seg_id: str, mode: str, days_shift: int = 0) -> dict:
    """Closure-day distribution (one value per past winter) for a real axis or a forward link."""
    status = {r["segment"]: r["status"] for r in db.query("SELECT segment, status FROM road_status")}
    if seg_id in ("NH1-ZOJILA", "NH3-BARALACHA"):
        pid = seg_id.split("-")[1]
        f, loc, scale, shift, kind = fit(pid), CLOSURES[pid]["weather"], 1.0, 0.0, "highway"
        reopen = _reopen_day(pid)
    else:
        link = db.query("SELECT * FROM links WHERE id = ?", (seg_id,))[0]
        alts = [r["alt_m"] for r in db.query("SELECT alt_m FROM nodes WHERE id IN (?, ?)",
                                              (link["from_node"], link["to_node"]))]
        if link["pass"]:
            alts += [r["alt_m"] for r in db.query("SELECT alt_m FROM passes WHERE id = ?", (link["pass"],))]
        k = CP["threshold_factor"]["v"][link["mode"]]
        base = fit("BARALACHA")  # forward routes behave like the Manali-Leh passes, at their own height
        f = {"C_cm": base["C_cm"] * k, "D_cm": base["D_cm"] * k, "T_c": base["T_c"]}
        loc, kind = "sector_x", link["mode"]
        scale = 1 + CP["snow_per_1000m"]["v"] * max(0, max(alts) - world.REF_ALT) / 1000
        shift = -world.LAPSE * (max(alts) - world.REF_ALT)  # temperature at the route's highest point
        reopen = _reopen_day("BARALACHA") + CP["track_reopen_lag_days"]["v"]
    today, mem = _members(loc, mode, scale, shift)
    t = -99.0 if f["T_c"] is None else f["T_c"]
    if status.get(seg_id) == "closed":
        days = np.full(len(mem), today)
    else:
        days = np.array([_closing_day(m, f["C_cm"], f["D_cm"], t, today) for m in mem])
        days = np.maximum(days + days_shift, today)  # what-if: everything closes `days_shift` days earlier/later
    return {"id": seg_id, "kind": kind, "status": status.get(seg_id, "open"), "today": today,
            "days": days, "reopen_day": reopen}


def _dist_km(a: dict, b: dict) -> float:
    return math.hypot((a["lat"] - b["lat"]) * 111, (a["lon"] - b["lon"]) * 111 * math.cos(math.radians(a["lat"])))


def _flyable_share() -> float:
    """Share of past winter days (Nov-Mar) inside the helicopter weather limits at the sector."""
    w = world.weather("sector_x", "demo")
    w = w[(w["source"] == "open_meteo") & pd.to_datetime(w.index).month.isin([11, 12, 1, 2, 3])]
    h = M["helicopter"]
    ok = ((w["gust_max_kmh"] <= h["max_wind_kmh"]["v"]) & (w["snowfall_cm"] <= h["max_snowfall_cm"]["v"])
          & (w["cloud_pct"] <= h["max_cloud_pct"]["v"]))
    return round(100 * float(ok.mean()), 0)


def _air(post: dict, nodes: dict) -> dict:
    """Helicopter from Leh to the post's helipad (or the nearest one, then porters)."""
    pads = [n for n in nodes.values() if n["helipad"] and n["kind"] != "depot"]
    pad = post if post["helipad"] else min(pads, key=lambda n: _dist_km(n, post))
    h = M["helicopter"]
    curve = np.array(h["payload_kg_by_alt_m"]["v"])
    payload = float(np.interp(pad["alt_m"], curve[:, 0], curve[:, 1]))
    hours = 2 * _dist_km(nodes["LEH"], pad) / h["speed_kmh"]["v"] + h["handling_hours"]["v"]
    per_kg = costs.heli_sortie(hours) / payload
    if pad is not post:  # last leg on foot
        per_kg += costs.foot_per_kg("porter", _dist_km(pad, post) * 1.4)
    return {"pad": pad["name"], "payload_kg": round(payload), "sortie_hours": round(hours, 2), "inr_per_kg": per_kg}


@functools.lru_cache(maxsize=8)
def run(mode: str = "demo", shift: int = 0, strength: tuple = ()) -> dict:
    """shift: what-if closure shift in days (e.g. -10). strength: what-if ((post, factor), ...)."""
    now = world.clock(mode).normalize()
    start = _season_start(now)
    date = lambda d: (start + int(d) * DAY).date().isoformat()
    q = 100 * (1 - CP["confidence"]["v"])  # 20th percentile: still open with 80% probability
    nodes = {n["id"]: n for n in db.query("SELECT * FROM nodes")}
    links = {l["to_node"]: l for l in db.query("SELECT * FROM links")}
    fc = forecast.forecast(mode, dict(strength)) if strength else forecast.run(mode)["forecast"]
    stock = world.stock(mode).set_index(["post", "class"])["qty"]
    flyable = _flyable_share()
    segs = {}
    items, curves = [], {}
    for post in sorted(i for i, n in nodes.items() if n["kind"] == "post"):
        route = [links[post], links[links[post]["from_node"]]]  # roadhead -> post, depot -> roadhead
        for l in route:
            segs.setdefault(l["id"], segment(l["id"], mode, shift))
        close = np.min([segs[l["id"]]["days"] for l in route], axis=0)
        reopen = max(segs[l["id"]]["reopen_day"] for l in route)
        today = segs[route[0]["id"]]["today"]
        km = {m: sum(l["km"] for l in route if l["mode"] == m) for m in ("road", "jeep_track", "mule_track")}
        hours = (km["road"] / M["truck"]["speed_kmh"]["v"] + km["jeep_track"] / M["truck"]["jeep_speed_kmh"]["v"]
                 + km["mule_track"] / M["mule"]["speed_kmh"]["v"])
        transit = math.ceil(hours / M["truck"]["drive_hours_per_day"]["v"])
        safe_day = int(np.percentile(close, q, method="lower"))
        last_safe = safe_day - transit - CP["loading_buffer_days"]["v"]
        road_per_kg = costs.road(km["road"], km["jeep_track"]) + costs.foot_per_kg("mule", km["mule_track"])
        air = _air(nodes[post], nodes)
        curves[post] = [{"date": date(today + i), "p_closed": round(float(np.mean(close <= today + i)), 2)}
                        for i in range(120)]
        by = "truck + mule" if km["mule_track"] else ("truck + jeep" if km["jeep_track"] else "truck")
        f = fc[(fc["post"] == post) & (fc["date"] < start + reopen * DAY)]
        for cls, c in P["classes"].items():
            g = f[f["class"] == cls]
            need, need_hi = float(g["p50"].sum()), float(g["p90"].sum())
            short = max(0.0, need - float(stock[(post, cls)]))
            short_kg = short * c["kg_per_unit"]
            sorties = math.ceil(short_kg / air["payload_kg"]) if short_kg else 0
            multiple = air["inr_per_kg"] / road_per_kg
            days_left = last_safe - today
            short_days = short / max(float(g["p50"].iloc[0]), 1e-9)  # the gap in days of today's use
            status = ("stocked" if short == 0 else "margin" if short_days < CP["margin_days"]["v"] else
                      "passed" if days_left < 0 else "urgent" if days_left <= 7 else "watch")
            name = f"{nodes[post]['name']} {c['label'].lower()}"
            if status == "stocked":
                headline = f"{name}: stocked until the route reopens (~{date(reopen)})."
            elif status == "margin":
                headline = (f"{name}: forecast gap of {short:,.0f} {c['unit']} (~{short_days:.0f} days of use) is "
                            f"within the {CP['margin_days']['v']}-day forecast margin; review at the next update.")
            elif status == "passed":
                headline = (f"{name}: the ground route is already closed or will close before a convoy arrives. "
                            f"Air maintenance needed now, ~{multiple:.0f}x the road cost "
                            f"({costs.basis(road_per_kg, air['inr_per_kg'])}).")
            else:
                headline = (f"{name}: last safe {by} dispatch {pd.Timestamp(date(last_safe)):%d %b} "
                            f"({CP['confidence']['v']:.0%} confidence). After that: air maintenance, ~{multiple:.0f}x cost "
                            f"({costs.basis(road_per_kg, air['inr_per_kg'])}).")
            items.append({
                "post": post, "post_name": nodes[post]["name"], "class": cls, "label": c["label"], "unit": c["unit"],
                "status": status, "headline": headline, "dispatch_by": by, "route": [l["id"] for l in route][::-1],
                "last_safe_dispatch": date(last_safe), "days_left": days_left, "transit_days": transit,
                "closure_p20": date(np.percentile(close, 20, method="lower")),
                "closure_p50": date(np.percentile(close, 50, method="lower")),
                "closure_p80": date(np.percentile(close, 80, method="lower")),
                "reopen_p80": date(reopen), "stock": round(float(stock[(post, cls)]), 1),
                "need_until_reopen": round(need, 1), "need_until_reopen_p90": round(need_hi, 1),
                "shortfall": round(short, 1), "shortfall_kg": round(short_kg),
                "road_inr_per_kg": round(road_per_kg, 1), "air_inr_per_kg": round(air["inr_per_kg"]),
                "cost_multiple": round(multiple), "cost_basis": costs.basis(road_per_kg, air["inr_per_kg"]),
                "cost_inputs": costs.INPUTS, "air_pad": air["pad"], "heli_payload_kg": air["payload_kg"],
                "heli_sorties": sorties, "heli_hours": round(sorties * air["sortie_hours"], 1),
                "air_cost_inr_lakh": round(short_kg * air["inr_per_kg"] / 1e5, 1),
                "flyable_winter_pct": flyable})
    axes = []
    for seg_id, name in (("NH1-ZOJILA", "NH-1 Zoji La (real)"), ("NH3-BARALACHA", "NH-3 Manali-Leh (real)")):
        s = segment(seg_id, mode, shift)
        axes.append({"id": seg_id, "name": name, "status": s["status"],
                     "closure_p20": date(np.percentile(s["days"], 20, method="lower")),
                     "closure_p50": date(np.percentile(s["days"], 50, method="lower")),
                     "closure_p80": date(np.percentile(s["days"], 80, method="lower")),
                     "no_closure_share": round(float(np.mean(s["days"] >= SEASON_DAYS)), 2),
                     "reopen_p80": date(s["reopen_day"]), "rule": fit(seg_id.split("-")[1])})
    order = {"passed": 0, "urgent": 1, "watch": 2, "margin": 3, "stocked": 4}
    items.sort(key=lambda r: (order[r["status"]], r["days_left"]))
    return {"items": items, "axes": axes, "curves": curves, "flyable_winter_pct": flyable,
            "winters_replayed": len(WINTERS), "confidence": CP["confidence"]["v"]}
