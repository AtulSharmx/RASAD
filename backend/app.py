"""RASAD API + the built web app, on http://localhost:8000 (this machine only)."""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend import adapters, db

app = FastAPI(title="RASAD", docs_url="/api/docs")


@app.get("/api/health")
def health():
    return {"ok": True, "now": db.PARAMS["demo"]["now"], "sector": db.SECTOR["label"],
            "note": "Runs fully on-premise. Simulated for prototype."}


@app.get("/api/sector")
def sector():
    return {"label": db.SECTOR["label"], "note": db.SECTOR["note"], "nodes": db.query("SELECT * FROM nodes"),
            "passes": db.query("SELECT * FROM passes"), "links": db.query("SELECT * FROM links"),
            "axes": db.SECTOR["axes"], "roads": db.query("SELECT * FROM road_status")}


@app.get("/api/stock")
def stock():
    return db.query("SELECT * FROM stock_now ORDER BY post, class")


@app.get("/api/sources")
def sources():
    return adapters.status()


@app.post("/api/sources/sync")
def sync():
    adapters.sync()
    return adapters.status()


dist = db.ROOT / "frontend" / "dist"
if dist.exists():  # must be last: serves the React app for every other path
    app.mount("/", StaticFiles(directory=dist, html=True), name="web")
