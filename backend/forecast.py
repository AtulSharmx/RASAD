"""Step 3: demand forecast per post and supply class, with a confidence band, plus days of cover.

Model: LightGBM quantile regression (P10 / P50 / P90) of the daily use PER PERSON. Inputs: weather at
the post (real, adjusted for its altitude), altitude, time of year and the post itself. Multiplying by
troop strength gives the post's demand, so a troop change flows straight into the forecast.
Honesty check: on the last 60 days the model never saw, compared with a naive "average of the last 28 days".
"""
import functools

import lightgbm as lgb
import numpy as np
import pandas as pd

from backend import db, world

QUANTILES = (0.1, 0.5, 0.9)
HOLDOUT_DAYS, NAIVE_DAYS = 60, 28
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


def _predict(models: dict, x: pd.DataFrame) -> np.ndarray:
    p = np.column_stack([models[q].predict(x[FEATURES]) for q in QUANTILES])
    return np.clip(np.sort(p, axis=1), 0, None)  # quantiles must not cross, use is never negative


def backtest(mode: str = "demo") -> pd.DataFrame:
    now = world.clock(mode).normalize()
    start = now - HOLDOUT_DAYS * DAY
    hist = _history(mode, _frame(mode, now - DAY))
    rows = []
    for cls, h in hist.groupby("class"):
        train, test = h[h["date"] < start], h[h["date"] >= start]
        p = _predict(_fit(train), test) * test["strength"].to_numpy()[:, None]
        recent = train[train["date"] >= start - NAIVE_DAYS * DAY].groupby("post")["qty"].mean()
        naive = test["post"].map(recent).to_numpy()
        actual = test["qty"].to_numpy()
        err = lambda pred: 100 * np.abs(pred - actual).sum() / actual.sum()  # WAPE
        rows.append({"class": cls, "label": db.PARAMS["classes"][cls]["label"],
                     "model_error_pct": round(err(p[:, 1]), 1), "naive_error_pct": round(err(naive), 1),
                     "band_coverage_pct": round(100 * np.mean((actual >= p[:, 0]) & (actual <= p[:, 2])), 1),
                     "test_from": start.date().isoformat(), "test_to": (now - DAY).date().isoformat()})
    out = pd.DataFrame(rows)
    out["plain"] = [
        f"{r.label}: on a typical day our forecast is off by {r.model_error_pct:.0f}%; the simple "
        f"'average of the last 4 weeks' is off by {r.naive_error_pct:.0f}%. {r.band_coverage_pct:.0f}% of "
        f"real days fell inside our band (aim: 80%)." for r in out.itertuples()]
    return out


def forecast(mode: str = "demo", strength_factor: dict | None = None) -> pd.DataFrame:
    """Daily P10/P50/P90 demand per post and class, from today to the end of the weather outlook.
    strength_factor: e.g. {"PA": 1.2} for a what-if troop increase."""
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
        p = _predict(_fit(h), fut) * fut["post"].map(strength).to_numpy()[:, None]
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


@functools.lru_cache(maxsize=4)
def run(mode: str = "demo") -> dict:
    """Everything the screens need; cached until the data changes (call run.cache_clear())."""
    fc = forecast(mode)
    return {"accuracy": backtest(mode), "forecast": fc, "cover": cover(mode, fc)}
