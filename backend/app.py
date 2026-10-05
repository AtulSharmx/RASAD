"""RASAD API + the built web app, on http://localhost:8000 (this machine only)."""
import json
import urllib.error

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from backend import adapters, closure, db, forecast, realdata, world

app = FastAPI(title="RASAD", docs_url="/api/docs")


def records(df) -> list[dict]:
    """DataFrame -> plain JSON rows (numpy numbers and dates made safe)."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.get("/api/health")
def health(mode: str = "demo"):
    return {"ok": True, "mode": mode, "now": world.clock(mode).isoformat(), "sector": db.SECTOR["label"],
            "note": "Runs fully on-premise. Military data is simulated; weather, terrain and roads are real."}


@app.get("/api/sector")
def sector():
    return {"label": db.SECTOR["label"], "note": db.SECTOR["note"], "nodes": db.query("SELECT * FROM nodes"),
            "passes": db.query("SELECT * FROM passes"), "links": db.query("SELECT * FROM links"),
            "axes": db.SECTOR["axes"], "roads": db.query("SELECT * FROM road_status"),
            "osm": [{**r, "geometry": json.loads(r["geometry"])} for r in db.query("SELECT * FROM geometry")]}


@app.get("/api/weather")
def weather(location: str = "sector_x", mode: str = "demo"):
    return world.weather(location, mode).reset_index().to_dict("records")


@app.post("/api/live/refresh")
def live_refresh():
    """Live mode: download a fresh 16-day forecast (needs internet). The old cache stays if offline."""
    try:
        realdata.fetch_forecast()
    except (urllib.error.URLError, TimeoutError) as e:
        raise HTTPException(503, f"No internet - still using the cached forecast ({e})")
    adapters.sync({"open_meteo_forecast"})
    clear_caches()
    return adapters.status()


def clear_caches() -> None:
    """Results depend on the data; recompute after any reload."""
    forecast.clear()
    closure.run.cache_clear()


@app.get("/api/pnr")
def pnr(mode: str = "demo"):
    """Point of No Return: closure windows, last safe dispatch and the cost of air after it."""
    return closure.run(mode)


@app.get("/api/forecast")
def forecast_summary(mode: str = "demo"):
    r = forecast.run(mode)
    return {"accuracy": records(r["accuracy"]), "cover": records(r["cover"]),
            "note": "Accuracy is measured on simulated consumption data; real accuracy is known only on real CICG data. "
                    "The method is chosen on the same 60 days it is scored on, so the score is slightly optimistic."}


@app.get("/api/forecast/{post}")
def forecast_post(post: str, mode: str = "demo", days: int = 60):
    """Last `days` of actual use and the next `days` of forecast (P10/P50/P90) for each class."""
    now = world.clock(mode).normalize()
    hist = world.consumption(mode)
    hist = hist[(hist["post"] == post) & (hist["date"] >= (now - pd.Timedelta(days=days)).date().isoformat())]
    fc = forecast.run(mode)["forecast"]
    fc = fc[(fc["post"] == post) & (fc["date"] < now + pd.Timedelta(days=days))]
    return {"actual": records(hist), "forecast": records(fc)}


@app.get("/api/stock")
def stock():
    return db.query("SELECT * FROM stock_now ORDER BY post, class")


@app.get("/api/sources")
def sources():
    return adapters.status()


@app.post("/api/sources/sync")
def sync():
    adapters.sync()
    clear_caches()
    return adapters.status()


dist = db.ROOT / "frontend" / "dist"
if dist.exists():  # must be last: serves the React app for every other path
    app.mount("/", StaticFiles(directory=dist, html=True), name="web")
