"""Step 3: demand forecast per post and supply class, with a confidence band, plus days of cover.

Model: LightGBM quantile regression (P10 / P50 / P90) of the daily use PER PERSON. Inputs: weather at
the post (real, adjusted for its altitude), altitude, time of year and the post itself. Multiplying by
troop strength gives the post's demand, so a troop change flows straight into the forecast.
Honesty check: on the last 60 days the model never saw, against the naive "28-day average". For each class
the better of the two is used, and its band is calibrated so it really holds ~80% of real days.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd

from backend import cache, db, world

QUANTILES = (0.1, 0.5, 0.9)
WINDOW, NAIVE_DAYS = 60, 28  # hold-out and calibration windows; naive look-back (days)
TARGET = 0.80  # share of real days the P10-P90 band should hold
MIN_GAIN = 1.0  # % points the model must beat the 28-day average by, or the simpler method is used
FEATURES = ["t_mean", "t_min", "snow", "doy_sin", "doy_cos", "alt", "post_i"]
LGB = {"learning_rate": 0.05, "num_leaves": 15, "min_data_in_leaf": 20, "verbose": -1, "seed": 42,
       "deterministic": True, "num_threads": 1}
ROUNDS = 300
DAY = pd.Timedelta(days=1)


def _frame(mode: str, end: pd.Timestamp) -> pd.DataFrame:
    """One row per post per day (history start .. end) with the features."""
    posts = db.query("SELECT id, alt_m FROM nodes WHERE kind = 'post' ORDER BY id")
    wx = world.weather("sector_x", mode)
    wx.index = pd.to_datetime(wx.index)
    days = pd.date_range(db.PARAMS["demo"]["history_start"], end)
    w = wx.reindex(days)
    frames = []
    for i, p in enumerate(posts):
        drop = world.LAPSE * (p["alt_m"] - world.REF_ALT)  # colder higher up
        frames.append(pd.DataFrame({
            "date": days, "post": p["id"], "post_i": i, "alt": p["alt_m"],
            "t_mean": ((w["tmax"] + w["tmin"]) / 2 - drop).to_numpy(),
            "t_min": (w["tmin"] - drop).to_numpy(), "snow": w["snowfall_cm"].to_numpy()}))
    f = pd.concat(frames, ignore_index=True)
    doy = 2 * np.pi * f["date"].dt.dayofyear / 365.25
    return f.assign(doy_sin=np.sin(doy), doy_cos=np.cos(doy))


def _history(mode: str, f: pd.DataFrame) -> pd.DataFrame:
    h = world.consumption(mode)
    h["date"] = pd.to_datetime(h["date"])
    return h.assign(rate=h["qty"] / h["strength"]).merge(f, on=["date", "post"])


def _fit(train: pd.DataFrame) -> dict:
    data = lgb.Dataset(train[FEATURES], train["rate"], categorical_feature=["post_i"], free_raw_data=False)
    return {q: lgb.train({**LGB, "objective": "quantile", "alpha": q}, data, ROUNDS) for q in QUANTILES}


def _model(train: pd.DataFrame, x: pd.DataFrame) -> np.ndarray:
    models = _fit(train)
    p = np.column_stack([models[q].predict(x[FEATURES]) for q in QUANTILES])
    return np.clip(np.sort(p, axis=1), 0, None)  # quantiles must not cross; use is never negative


def _naive(train: pd.DataFrame, x: pd.DataFrame) -> np.ndarray:
    """28-day average use per person (P50), with the 10th / 90th percentile days as the band."""
    last = train[train["date"] > train["date"].max() - NAIVE_DAYS * DAY].groupby("post")["rate"]
    q = pd.DataFrame({"p10": last.quantile(0.1), "p50": last.mean(), "p90": last.quantile(0.9)})
    return np.sort(q.reindex(x["post"]).to_numpy(), axis=1)


METHODS = {"model": ("LightGBM model", _model), "naive": ("28-day average", _naive)}


def _widen(p: np.ndarray, k: float) -> np.ndarray:
    mid = p[:, 1]
    return np.column_stack([mid - k * (mid - p[:, 0]), mid, mid + k * (p[:, 2] - mid)]).clip(0)


def _coverage(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((y >= p[:, 0]) & (y <= p[:, 2])))


def _calibrate(p: np.ndarray, y: np.ndarray) -> float:
    """Smallest band-widening factor that makes the band hold TARGET of the real days."""
    for k in np.arange(0.5, 6.001, 0.05):
        if _coverage(_widen(p, k), y) >= TARGET:
            return round(float(k), 2)
    return 6.0


@cache.memo(maxsize=4)
def evaluate(mode: str = "demo") -> tuple[pd.DataFrame, dict]:
    """Two windows, no leak:
    - SELECT window (the 60 days before the final 60): pick the method per class and set its band factor.
    - TEST window (the final 60 days, never used for any choice): report error and coverage.
    The live forecast then re-fits the band factor on the latest 60 days."""
    now = world.clock(mode).normalize()
    hold, sel = now - WINDOW * DAY, now - 2 * WINDOW * DAY
    hist = _history(mode, _frame(mode, now - DAY))
    wape = lambda p, d: 100 * np.abs(p[:, 1] * d["strength"].to_numpy() - d["qty"].to_numpy()).sum() / d["qty"].sum()
    rows, choice = [], {}
    for cls, h in hist.groupby("class"):
        sel_set, test = h[(h["date"] >= sel) & (h["date"] < hold)], h[h["date"] >= hold]
        y = test["rate"].to_numpy()
        res = {}
        for m, (_, fn) in METHODS.items():
            raw_sel = fn(h[h["date"] < sel], sel_set)
            k_sel = _calibrate(raw_sel, sel_set["rate"].to_numpy())
            raw = fn(h[h["date"] < hold], test)
            res[m] = {"sel_error": wape(raw_sel, sel_set), "error": wape(raw, test),
                      "cov_raw": 100 * _coverage(raw, y), "cov": 100 * _coverage(_widen(raw, k_sel), y),
                      "k": _calibrate(raw, y)}
        gain = res["naive"]["sel_error"] - res["model"]["sel_error"]
        use = "model" if gain >= MIN_GAIN else "naive"
        choice[cls] = (use, res[use]["k"])
        if use == "model":
            why = (f"on the earlier 60 days it was {gain:.0f} percentage point{'' if round(gain) == 1 else 's'} "
                   "more accurate than the 28-day average")
        else:
            why = (f"on the earlier 60 days the model was not clearly better ({res['model']['sel_error']:.0f}% vs "
                   f"{res['naive']['sel_error']:.0f}% error), so the simpler method is used")
        label, r = db.PARAMS["classes"][cls]["label"], res[use]
        rows.append({
            "class": cls, "label": label, "method": METHODS[use][0], "why": why,
            "select_model_error_pct": round(res["model"]["sel_error"], 1),
            "select_naive_error_pct": round(res["naive"]["sel_error"], 1),
            "model_error_pct": round(res["model"]["error"], 1), "naive_error_pct": round(res["naive"]["error"], 1),
            "error_pct": round(r["error"], 1), "coverage_before_pct": round(r["cov_raw"], 1),
            "coverage_pct": round(r["cov"], 1), "band_factor": r["k"],
            "select_from": sel.date().isoformat(), "select_to": (hold - DAY).date().isoformat(),
            "test_from": hold.date().isoformat(), "test_to": (now - DAY).date().isoformat(),
            "plain": f"{label}: using the {METHODS[use][0]} because {why}. On the final 60 days (not used for any "
                     f"choice) its typical daily error was {r['error']:.0f}% and {r['cov']:.0f}% of real days fell "
                     "inside the band (aim: 80%)."})
    return pd.DataFrame(rows), choice


def forecast(mode: str = "demo", strength_factor: dict | None = None) -> pd.DataFrame:
    """Daily P10/P50/P90 demand per post and class, from today to the end of the weather outlook.
    strength_factor: e.g. {"PA": 1.2} for a what-if troop increase."""
    _, choice = evaluate(mode)
    now = world.clock(mode).normalize()
    end = pd.Timestamp(max(world.weather("sector_x", mode).index))
    f = _frame(mode, end)
    hist = _history(mode, f)
    strength = hist.sort_values("date").groupby("post")["strength"].last().astype(float)
    for post, k in (strength_factor or {}).items():
        strength[post] *= k
    fut = f[f["date"] >= now]
    out = []
    for cls, h in hist.groupby("class"):
        use, k = choice[cls]
        p = _widen(METHODS[use][1](h, fut), k) * fut["post"].map(strength).to_numpy()[:, None]
        out.append(fut[["date", "post"]].assign(**{"class": cls, "p10": p[:, 0], "p50": p[:, 1], "p90": p[:, 2]}))
    return pd.concat(out, ignore_index=True)


def cover(mode: str, fc: pd.DataFrame) -> pd.DataFrame:
    """Days of cover = days until the forecast demand, added up day by day, is more than the stock.
    'low' uses P90 demand (bad case), 'high' uses P10 demand (good case)."""
    stock = world.stock(mode).set_index(["post", "class"])
    rows = []
    for (post, cls), g in fc.sort_values("date").groupby(["post", "class"]):
        s = float(stock.loc[(post, cls), "qty"])
        days = {b: int((g[b].cumsum() <= s).sum()) for b in ("p10", "p50", "p90")}
        rows.append({"post": post, "class": cls, "stock": round(s, 1), "unit": db.PARAMS["classes"][cls]["unit"],
                     "use_today_p50": round(float(g["p50"].iloc[0]), 1), "days": days["p50"],
                     "days_low": days["p90"], "days_high": days["p10"], "horizon_days": len(g),
                     "runs_out": (g["date"].iloc[0] + days["p50"] * DAY).date().isoformat()
                     if days["p50"] < len(g) else None})
    out = pd.DataFrame(rows)
    red, amber = db.PARAMS["cover"]["red_days"]["v"], db.PARAMS["cover"]["amber_days"]["v"]
    out["status"] = np.select([out["days_low"] < red, out["days_low"] < amber], ["red", "amber"], "green")
    return out


@cache.memo(maxsize=4)
def run(mode: str = "demo") -> dict:
    """Everything the screens need; cached until the data changes (then call clear())."""
    fc = forecast(mode)
    return {"accuracy": evaluate(mode)[0], "forecast": fc, "cover": cover(mode, fc)}


def clear() -> None:
    run.cache_clear()
    evaluate.cache_clear()
