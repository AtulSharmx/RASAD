"""SQLite: one file, data/rasad.db. Master data (sector) comes from data/sector.json."""
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "rasad.db"
SECTOR = json.loads((ROOT / "data" / "sector.json").read_text(encoding="utf-8"))
PARAMS = json.loads((ROOT / "data" / "params.json").read_text(encoding="utf-8"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, name TEXT, kind TEXT, lat REAL, lon REAL,
    alt_m REAL, fictional INTEGER, helipad INTEGER, troops INTEGER);
CREATE TABLE IF NOT EXISTS passes(id TEXT PRIMARY KEY, name TEXT, lat REAL, lon REAL, alt_m REAL,
    axis TEXT, fictional INTEGER, weather TEXT);
CREATE TABLE IF NOT EXISTS links(id TEXT PRIMARY KEY, from_node TEXT, to_node TEXT, mode TEXT,
    km REAL, pass TEXT);
CREATE TABLE IF NOT EXISTS stock(post TEXT NOT NULL, class TEXT NOT NULL, qty REAL NOT NULL,
    unit TEXT, as_of TEXT NOT NULL, source TEXT);
CREATE TABLE IF NOT EXISTS consumption(date TEXT NOT NULL, post TEXT NOT NULL, class TEXT NOT NULL,
    qty REAL NOT NULL, strength INTEGER, source TEXT);
CREATE TABLE IF NOT EXISTS weather(date TEXT NOT NULL, location TEXT NOT NULL, tmax REAL, tmin REAL,
    snowfall_cm REAL, precip_mm REAL, snow_depth_m REAL, wind_max_kmh REAL, gust_max_kmh REAL,
    cloud_pct REAL, wcode INTEGER, simulated INTEGER NOT NULL, source TEXT);
CREATE TABLE IF NOT EXISTS road_status(segment TEXT NOT NULL, status TEXT NOT NULL, reason TEXT,
    updated TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS airlift(date TEXT NOT NULL, sortie TEXT, aircraft TEXT, base TEXT,
    hours REAL NOT NULL, tasked_to TEXT, source TEXT);
CREATE TABLE IF NOT EXISTS source_runs(source TEXT, ts TEXT, ok INTEGER, records INTEGER,
    rejected INTEGER, last_record TEXT, error TEXT);
CREATE INDEX IF NOT EXISTS ix_cons ON consumption(post, class, date);
CREATE INDEX IF NOT EXISTS ix_wx ON weather(location, date);

-- current stock = newest reading per post and class, whichever source sent it
CREATE VIEW IF NOT EXISTS stock_now AS
SELECT s.* FROM stock s JOIN (SELECT post, class, MAX(as_of) m FROM stock GROUP BY post, class) x
  ON s.post = x.post AND s.class = x.class AND s.as_of = x.m;
"""


def connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def query(sql: str, args=()) -> list[dict]:
    with connect() as con:
        return [dict(r) for r in con.execute(sql, args)]


def columns(table: str) -> list[str]:
    with connect() as con:
        return [r["name"] for r in con.execute(f"PRAGMA table_info({table})")]


def init(reset: bool = False) -> None:
    if reset:
        DB_PATH.unlink(missing_ok=True)
    with connect() as con:
        con.executescript(SCHEMA)
        con.execute("DELETE FROM nodes")
        con.execute("DELETE FROM passes")
        con.execute("DELETE FROM links")
        con.executemany(
            "INSERT INTO nodes VALUES(:id,:name,:kind,:lat,:lon,:alt_m,:fictional,:helipad,:troops)",
            SECTOR["nodes"])
        con.executemany(
            "INSERT INTO passes VALUES(:id,:name,:lat,:lon,:alt_m,:axis,:fictional,:weather)",
            SECTOR["passes"])
        con.executemany(
            "INSERT INTO links VALUES(:id,:from,:to,:mode,:km,:pass)", SECTOR["links"])
