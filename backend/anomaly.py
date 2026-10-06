"""Step 9: consumption anomaly alerts (and silent IoT sensors).

For every post and supply, the weather-aware model says how much use per person to EXPECT on each past day
(median model, the same inputs as the forecast). Days where actual use is far above that are grouped:
- one day far above, then normal again    -> likely a data-entry error;
- several days moderately above           -> unexplained steady excess (check for a leak or pilferage);
- several days far above                  -> a sharp surge (could be genuine need; confirm with the post).
Thresholds scale with each series' own day-to-day noise, so a noisy item (medicine) needs a bigger jump.
"""

import lightgbm as lgb
import numpy as np
import pandas as pd

from backend import adapters, cache, db, forecast, world

SPIKE_SIGMA, SPIKE_MIN_RATIO = 5, 3.0  # one-day jump: 5 noise widths and at least 3x
# several days: the 7-day MEDIAN must sit 2 noise widths high (so at least 4 of 7 days are high; one spike cannot do it)
RUN_DAYS, RUN_SIGMA, RUN_MIN_RATIO, SURGE_RATIO = 7, 2.0, 1.2, 2.0


def _expected(h: pd.DataFrame) -> np.ndarray:
    """Median (P50) use per person that weather, height, season and post explain."""
    data = lgb.Dataset(h[forecast.FEATURES], h["rate"], categorical_feature=["post_i"])
    m = lgb.train({**forecast.LGB, "objective": "quantile", "alpha": 0.5}, data, forecast.ROUNDS)
    return np.clip(m.predict(h[forecast.FEATURES]), 1e-6, None)


def _episodes(mask: np.ndarray) -> list[tuple[int, int]]:
    out, start = [], None
    for i, on in enumerate(list(mask) + [False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            out.append((start, i - 1))
            start = None
    return out


@cache.memo(maxsize=4)
def run(mode: str = "demo") -> list[dict]:
    now = world.clock(mode).normalize()
    hist = forecast._history(mode, forecast._frame(mode, now - forecast.DAY))
    names = {n["id"]: n["name"] for n in db.query("SELECT id, name FROM nodes")}
    alerts = []
    for cls, h in hist.groupby("class"):
        h = h.sort_values(["post", "date"]).reset_index(drop=True)
        h["exp"] = _expected(h)
        c = db.PARAMS["classes"][cls]
        for post, g in h.groupby("post"):
            r = np.log(g["rate"].to_numpy() / g["exp"].to_numpy())  # log of actual / expected
            s = max(1.4826 * np.median(np.abs(r - np.median(r))), 0.03)  # robust day-to-day noise
            dates, qty, exp_qty = g["date"].to_numpy(), g["qty"].to_numpy(), (g["exp"] * g["strength"]).to_numpy()
            roll = pd.Series(r).rolling(RUN_DAYS, center=True, min_periods=RUN_DAYS).median().to_numpy()
            run_mask = np.nan_to_num(roll) > max(RUN_SIGMA * s, np.log(RUN_MIN_RATIO))
            spike_mask = (r > SPIKE_SIGMA * s) & (r > np.log(SPIKE_MIN_RATIO)) & ~run_mask
            for kind_mask, is_run in ((run_mask, True), (spike_mask, False)):
                for a, b in _episodes(kind_mask):
                    if is_run:  # the rolling window blurs the edges: keep the days that are actually high
                        hi = [i for i in range(max(0, a - RUN_DAYS // 2), min(len(r), b + RUN_DAYS // 2 + 1)) if r[i] > 1.5 * s]
                        if not hi:
                            continue
                        a, b = hi[0], hi[-1]
                    ratio = float(qty[a:b + 1].sum() / exp_qty[a:b + 1].sum())
                    extra = float(qty[a:b + 1].sum() - exp_qty[a:b + 1].sum())
                    days = b - a + 1
                    d0, d1 = pd.Timestamp(dates[a]), pd.Timestamp(dates[b])
                    when = f"{d0:%d %b}" if days == 1 else f"{d0:%d %b} to {d1:%d %b}"
                    who = f"{names[post]} {c['label'].lower()}"
                    if not is_run:
                        kind, plain = "data error", (f"Possible data-entry error — verify on ground. {who}: on {when} the record shows "
                                                     f"{ratio:.1f}× the usual use, then normal again; check that day's entry against the post's issue register.")
                    elif ratio >= SURGE_RATIO:
                        kind, plain = "sharp surge", (f"Possible genuine surge in need — verify on ground. {who}: {days} days ({when}) at "
                                                      f"{ratio:.1f}× the expected use; confirm the reason with the post.")
                    else:
                        kind, plain = "steady excess", (f"Possible leak, unrecorded issue or pilferage — verify on ground. {who}: {days} days "
                                                        f"({when}) at {ratio:.2f}× what the weather and season explain (+{extra:,.0f} {c['unit']}); "
                                                        "check the store and the issue register.")
                    alerts.append({"post": post, "post_name": names[post], "class": cls, "label": c["label"], "unit": c["unit"],
                                   "kind": kind, "start": str(d0.date()), "end": str(d1.date()), "days": days,
                                   "ratio": round(ratio, 2), "extra": round(extra, 1), "plain": plain})
    # sensors that stopped reporting (from the IoT adapter's health check)
    for s in adapters.status():
        if s["id"] != "iot_fuel":
            continue
        last = {r["post"]: r["as_of"] for r in db.query("SELECT post, as_of FROM stock WHERE source = 'iot_fuel'")}
        for note in s["notes"]:
            if "silent" not in note:
                continue
            for post in note.split(": ", 1)[1].split(", "):
                hours = (pd.Timestamp(db.PARAMS["demo"]["now"]) - pd.Timestamp(last[post])).total_seconds() / 3600
                alerts.append({"post": post, "post_name": names[post], "class": "kerosene", "label": "Kerosene / fuel", "unit": "L",
                               "kind": "silent sensor", "start": last[post][:10], "end": last[post][:10], "days": 0, "ratio": None,
                               "extra": None, "plain": f"Possible sensor or power fault — verify on ground. The fuel-tank sensor at {names[post]} has "
                               f"been silent for {hours:.0f} hours (last reading {pd.Timestamp(last[post]):%d %b %H:%M}); until it reports again, "
                               "RASAD uses the inventory figure."})
    order = {"silent sensor": 0, "steady excess": 1, "sharp surge": 2, "data error": 3}
    return sorted(alerts, key=lambda a: (order[a["kind"]], a["start"]), reverse=False)
