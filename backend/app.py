"""RASAD API + the built web app, on http://localhost:8000 (this machine only)."""
import contextlib
import json
import threading
import urllib.error
from typing import Literal

import pandas as pd
from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import adapters, anomaly, closure, costs, db, drones, forecast, planner, realdata, scenarios, world

def warm_up() -> None:
    """Pre-compute the demo results in the background so the screens open instantly."""
    try:
        closure.run("demo")  # first: the dashboard's risk posts need it (requests arriving meanwhile wait for it)
        planner.run("demo")
        scenarios.all_runs("demo")
    except Exception as e:  # never block start-up; the endpoints will show the error
        print("warm-up failed:", e)


@contextlib.asynccontextmanager
async def lifespan(_app):
    threading.Thread(target=warm_up, daemon=True).start()
    yield


app = FastAPI(title="RASAD", docs_url="/api/docs", lifespan=lifespan)
Mode = Literal["demo", "live"]  # only two modes: anything else is refused (each mode is cached and costly)
Location = Literal["leh", "kargil", "drass", "zojila", "baralacha", "tanglang", "sector_x"]


def records(df) -> list[dict]:
    """DataFrame -> plain JSON rows (numpy numbers and dates made safe)."""
    return json.loads(df.to_json(orient="records", date_format="iso"))


@app.get("/api/health")
def health(mode: Mode = "demo"):
    return {"ok": True, "mode": mode, "now": world.clock(mode).isoformat(), "sector": db.SECTOR["label"],
            "note": "Runs fully on-premise. Military data, posts and forward tracks are simulated; weather, terrain, "
                    "national highways and pass-closure dates are real."}


@app.get("/api/sector")
def sector():
    return {"label": db.SECTOR["label"], "note": db.SECTOR["note"], "nodes": db.query("SELECT * FROM nodes"),
            "passes": db.query("SELECT * FROM passes"), "links": db.query("SELECT * FROM links"),
            "axes": db.SECTOR["axes"], "roads": db.query("SELECT * FROM road_status"),
            "osm": [{**r, "geometry": json.loads(r["geometry"])} for r in db.query("SELECT * FROM geometry")]}


@app.get("/api/terrain")
def terrain():
    """Real Copernicus DEM grid (heights in m) for the offline relief map."""
    g = realdata.GRID
    pts = db.query("SELECT lat, lon, elev_m FROM terrain WHERE id = 'grid'")
    return {"lat0": g["lat"][0], "lon0": g["lon"][0], "lat1": g["lat"][1], "lon1": g["lon"][1], "step": g["step"],
            "points": [[p["lat"], p["lon"], p["elev_m"]] for p in pts]}


@app.get("/api/weather")
def weather(location: Location = "sector_x", mode: Mode = "demo"):
    return world.weather(location, mode).reset_index().to_dict("records")


@app.post("/api/live/refresh")
def live_refresh():
    """Live mode: download a fresh 16-day forecast (needs internet). The old cache stays if offline."""
    try:
        realdata.fetch_forecast()
    except (urllib.error.URLError, TimeoutError, OSError):
        cached = pd.Timestamp(realdata.FORECAST.stat().st_mtime, unit="s").strftime("%d %b %Y") if realdata.FORECAST.exists() else "none"
        raise HTTPException(503, f"No internet connection. RASAD keeps using the saved forecast (downloaded {cached}).")
    adapters.sync({"open_meteo_forecast"})
    clear_caches()
    return adapters.status()


def clear_caches() -> None:
    """Results depend on the data; recompute after any reload, starting at once in the background."""
    forecast.clear()
    closure.run.cache_clear()
    planner.run.cache_clear()
    drones.advise.cache_clear()
    anomaly.run.cache_clear()
    scenarios.run.cache_clear()
    threading.Thread(target=warm_up, daemon=True).start()


@app.get("/api/pnr")
def pnr(mode: Mode = "demo"):
    """Point of No Return: closure windows, last safe dispatch and the cost of air after it."""
    return closure.run(mode)


@app.get("/api/plan")
def plan(mode: Mode = "demo"):
    """Mixed-fleet plan for the next 7 days, with the current Approve / Modify / Reject status of each line."""
    return planner.with_decisions(planner.run(mode))


# DEMO ONLY: role and user come from the on-screen role picker, because the brief asks for demo roles
# with no real login. Anyone who can reach this API can claim any role. In deployment, take role and user
# from the authenticated identity (Army SSO / PKI) and map roles on the server; never trust the body.
class Decision(BaseModel):
    key: str = Field(max_length=200)
    action: str = Field(pattern="^(approve|modify|reject)$")
    role: str = Field(pattern="^(Commander|Logistics Officer|Post QM)$")
    user: str = Field(min_length=1, max_length=60)
    kg: float | None = Field(default=None, ge=0)
    note: str = Field(default="", max_length=500)


@app.post("/api/plan/decision")
def decision(d: Decision, mode: Mode = "demo"):
    try:
        return planner.decide(mode, d.key, d.action, d.role, d.user, d.kg, d.note)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except KeyError as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/audit")
def audit(limit: int = Query(200, ge=1, le=1000)):
    return db.query("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (min(limit, 1000),))


@app.get("/api/drones")
def drone_advisor(mode: Mode = "demo", n: int = Query(20, ge=1, le=500),
                  band: Literal["up_to_6000ft", "6000_12000ft", "12000_20000ft"] = "12000_20000ft"):
    """Where should N new drones of a band be based? Ranked by what they save this week."""
    return drones.advise(mode, n, band)


@app.get("/api/scenarios")
def what_ifs(mode: Mode = "demo"):
    """The four one-click what-ifs, each with before vs after."""
    return scenarios.all_runs(mode)


@app.get("/api/alerts")
def alerts(mode: Mode = "demo"):
    """Unusual consumption (data errors, unexplained excess, surges) and silent IoT sensors."""
    return anomaly.run(mode)


@app.get("/api/costs")
def cost_inputs():
    """The single set of cost inputs used everywhere, with source and PLACEHOLDER tag."""
    return costs.INPUTS


@app.get("/api/forecast")
def forecast_summary(mode: Mode = "demo"):
    r = forecast.run(mode)
    return {"accuracy": records(r["accuracy"]), "cover": records(r["cover"]),
            "note": "Accuracy is measured on simulated consumption data; real accuracy is known only on real CICG data. "
                    "The method and band are chosen on an earlier 60-day window; the score is from the final 60 days only."}


@app.get("/api/forecast/{post}")
def forecast_post(post: str = Path(max_length=10), mode: Mode = "demo", days: int = Query(60, ge=1, le=365)):
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


@app.middleware("http")
async def fresh_page(request, call_next):
    """The page itself is never cached, so a rebuilt UI shows at once; hashed /assets files may be."""
    resp = await call_next(request)
    if not request.url.path.startswith(("/api/", "/assets/")):
        resp.headers["Cache-Control"] = "no-cache"
    return resp


dist = db.ROOT / "frontend" / "dist"
if dist.exists():  # must be last: serves the React app for every other path
    app.mount("/", StaticFiles(directory=dist, html=True), name="web")
