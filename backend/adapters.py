"""USP D: source adapters.

Every data stream is described by ONE config file in sources/. A generic adapter reads it
(CSV / JSON / JSON-lines), renames the columns, translates codes, and loads the result into
the database. Adding a new stream = adding one config file. No app code changes.
"""
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from backend import db

SOURCES_DIR = db.ROOT / "sources"
TARGETS = {"stock", "consumption", "weather", "road_status", "airlift"}


def configs() -> list[dict]:
    out = []
    for f in sorted(SOURCES_DIR.glob("*.json")):
        cfg = json.loads(f.read_text(encoding="utf-8"))
        cfg["_file"] = f"sources/{f.name}"
        out.append(cfg)
    return out


def read(cfg: dict) -> pd.DataFrame:
    files = sorted(db.ROOT.glob(cfg["path"]))
    if not files:
        raise FileNotFoundError(f"no file matches {cfg['path']}")
    frames = []
    for f in files:
        if cfg["format"] == "csv":
            frames.append(pd.read_csv(f, dtype=str))
        elif cfg["format"] == "jsonl":
            frames.append(pd.read_json(f, lines=True, dtype=False, convert_dates=False))
        elif cfg["format"] == "json":
            data = json.loads(f.read_text(encoding="utf-8"))
            frames.append(pd.json_normalize(data[cfg["records"]] if cfg.get("records") else data))
        else:
            raise ValueError(f"unknown format {cfg['format']}")
    return pd.concat(frames, ignore_index=True)


def transform(df: pd.DataFrame, cfg: dict, target_cols: list[str]) -> tuple[pd.DataFrame, int]:
    """Returns (clean rows, number of rejected rows)."""
    df = df.rename(columns={src: dst for dst, src in cfg.get("map", {}).items()})
    for col, value in cfg.get("const", {}).items():
        df[col] = value
    rejected = 0
    for col, codes in cfg.get("value_map", {}).items():
        mapped = df[col].map(codes)
        rejected += int(mapped.isna().sum())  # unknown codes are refused, not guessed
        df = df.assign(**{col: mapped}).dropna(subset=[col])
    if cfg.get("latest_by"):
        df = df.sort_values(cfg["time_field"]).groupby(cfg["latest_by"]).tail(1)
    df["source"] = cfg["id"]
    keep = [c for c in target_cols if c in df.columns]
    missing = {"stock": ["post", "class", "qty", "as_of"], "consumption": ["date", "post", "class", "qty"],
               "weather": ["date", "location", "simulated"], "road_status": ["segment", "status"],
               "airlift": ["date", "hours"]}[cfg["target"]]
    missing = [c for c in missing if c not in keep]
    if missing:
        raise ValueError(f"config does not provide required fields: {missing}")
    return df[keep], rejected


def sync(only: str | None = None) -> None:
    now = datetime.now().isoformat(timespec="seconds")
    for cfg in configs():
        if only and cfg["id"] != only:
            continue
        run = {"source": cfg["id"], "ts": now, "ok": 0, "records": 0, "rejected": 0,
               "last_record": None, "error": None}
        try:
            if cfg["target"] not in TARGETS:
                raise ValueError(f"unknown target {cfg['target']}")
            df, run["rejected"] = transform(read(cfg), cfg, db.columns(cfg["target"]))
            with db.connect() as con:
                con.execute(f"DELETE FROM {cfg['target']} WHERE source = ?", (cfg["id"],))
                df.to_sql(cfg["target"], con, if_exists="append", index=False)
            run.update(ok=1, records=len(df), last_record=df[cfg["time_field"]].max())
        except Exception as e:  # a broken source must not stop the others
            run["error"] = f"{type(e).__name__}: {e}"
        with db.connect() as con:
            con.execute("INSERT INTO source_runs VALUES(:source,:ts,:ok,:records,:rejected,:last_record,:error)", run)


def status() -> list[dict]:
    """Health of every source for the Sources page (times compared with the demo clock)."""
    now = pd.Timestamp(db.PARAMS["demo"]["now"])
    out = []
    for cfg in configs():
        runs = db.query("SELECT * FROM source_runs WHERE source = ? ORDER BY rowid DESC LIMIT 1", (cfg["id"],))
        run = runs[0] if runs else None
        health, notes = "ok", []
        if not run:
            health, notes = "never synced", ["not loaded yet"]
        elif not run["ok"]:
            health, notes = "error", [run["error"]]
        else:
            if run["rejected"]:
                health = "warning"
                notes.append(f"{run['rejected']} rows refused (unknown codes)")
            limit = cfg.get("stale_after_hours")
            if limit:
                age_h = (now - pd.Timestamp(run["last_record"])).total_seconds() / 3600
                if age_h > limit:
                    health = "stale"
                    notes.append(f"newest record is {age_h:.0f} h old (limit {limit} h)")
                if cfg.get("latest_by"):  # e.g. one silent sensor among many
                    rows = db.query(f"SELECT {cfg['latest_by'][0]} k, {cfg['time_field']} t FROM {cfg['target']} "
                                    "WHERE source = ?", (cfg["id"],))
                    silent = [r["k"] for r in rows if (now - pd.Timestamp(r["t"])).total_seconds() / 3600 > limit]
                    if silent:
                        health = "warning" if health == "ok" else health
                        notes.append(f"{len(silent)} of {len(rows)} {cfg.get('key_label', 'keys')} silent > {limit} h: "
                                     + ", ".join(silent))
        out.append({
            "id": cfg["id"], "name": cfg["name"], "owner": cfg.get("owner", ""),
            "simulated": cfg.get("simulated", True), "target": cfg["target"], "health": health,
            "notes": notes, "last_sync": run and run["ts"], "last_record": run and run["last_record"],
            "records": run and run["records"], "file": cfg["_file"],
            "config": (db.ROOT / cfg["_file"]).read_text(encoding="utf-8"),
        })
    return out
