"""What the app sees as 'now', in two modes.

- demo: clock = 25 Oct 2026 06:00. Weather = real archive, then the simulated outlook (Oct 2021 copy).
- live: clock = today. Weather = real archive, then the REAL 16-day Open-Meteo forecast, then the outlook.
Military data (stock, consumption) is simulated in both modes.
"""
import pandas as pd

from backend import db

MODES = ("demo", "live")


def clock(mode: str = "demo") -> pd.Timestamp:
    return pd.Timestamp.now().floor("h") if mode == "live" else pd.Timestamp(db.PARAMS["demo"]["now"])


def weather(location: str, mode: str = "demo") -> pd.DataFrame:
    """One row per day (index = date string), best source first."""
    rank = {"open_meteo": 0, "open_meteo_forecast": 1, "met_outlook": 2}
    if mode != "live":
        del rank["open_meteo_forecast"]
    df = pd.DataFrame(db.query("SELECT * FROM weather WHERE location = ?", (location,)))
    df = df[df["source"].isin(rank)].assign(rank=lambda d: d["source"].map(rank))
    return df.sort_values(["date", "rank"]).drop_duplicates("date").drop(columns="rank").set_index("date")


def consumption(mode: str = "demo") -> pd.DataFrame:
    """Daily history strictly before the clock's day."""
    return pd.DataFrame(db.query("SELECT date, post, class, qty, strength FROM consumption WHERE date < ?",
                                 (clock(mode).date().isoformat(),)))


def stock(mode: str = "demo") -> pd.DataFrame:
    """Stock held at the clock time. The simulated world is built for the demo date, so in Live mode
    (earlier) we add back what the simulation says was used in between."""
    s = pd.DataFrame(db.query("SELECT post, class, qty, unit, as_of, source FROM stock_now"))
    now, demo = clock(mode), clock("demo")
    if now < demo:  # ponytail: assumes no deliveries in between; fine while Live mode is before the demo date
        used = pd.DataFrame(db.query(
            "SELECT post, class, SUM(qty) used FROM consumption WHERE date >= ? AND date < ? GROUP BY post, class",
            (now.date().isoformat(), demo.date().isoformat())), columns=["post", "class", "used"])
        s = s.merge(used, how="left", on=["post", "class"]).fillna({"used": 0})
        s["qty"] = s["qty"] + s.pop("used")
        s["as_of"] = now.isoformat()
    return s
