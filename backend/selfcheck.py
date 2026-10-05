"""Quick check of the core logic. Run after gen_data: python -m backend.selfcheck"""
import pandas as pd

from backend import adapters, db, world


def check_adapters():
    by_id = {s["id"]: s for s in adapters.status()}
    assert all(s["health"] != "error" for s in by_id.values()), [s["notes"] for s in by_id.values()]
    assert "PH" in " ".join(by_id["iot_fuel"]["notes"]), "Hotel's silent sensor should be flagged"
    now = {(r["post"], r["class"]): r for r in db.query("SELECT * FROM stock_now")}
    assert now[("PA", "kerosene")]["source"] == "iot_fuel", "newest reading (sensor) should win"
    assert now[("PH", "kerosene")]["source"] == "cicg_stock", "silent sensor must not win"
    # unknown codes are refused, not guessed
    cfg = {"id": "t", "target": "stock", "map": {}, "value_map": {"class": {"SKO": "kerosene"}}}
    df = pd.DataFrame({"post": ["PA", "PA"], "class": ["SKO", "XYZ"], "qty": [1, 2], "as_of": ["a", "b"]})
    out, rejected = adapters.transform(df, cfg, db.columns("stock"))
    assert len(out) == 1 and rejected == 1


def check_demo_story():
    cons = pd.DataFrame(db.query("SELECT post, class, qty FROM consumption WHERE date > '2026-09-26'"))
    rate = cons.groupby(["post", "class"])["qty"].mean()
    stock = {(r["post"], r["class"]): r["qty"] for r in db.query("SELECT * FROM stock_now")}
    days = {k: stock[k] / rate[k] for k in stock}
    assert 7 <= days[("PA", "kerosene")] <= 11, days[("PA", "kerosene")]
    assert days[("PD", "medical")] <= 4
    assert days[("PF", "rations")] <= 14
    assert sum(d < 30 for d in days.values()) == 3, "exactly three short items"


def check_real_data():
    by_id = {s["id"]: s for s in adapters.status()}
    for i in ("open_meteo", "open_meteo_forecast", "copernicus_dem", "osm"):
        assert by_id[i]["health"] == "ok" and by_id[i]["label"] == "Real data", by_id[i]
    assert by_id["cicg_stock"]["label"].startswith("Simulated — military data is classified")
    dem = {r["id"]: r["elev_m"] for r in db.query("SELECT id, elev_m FROM terrain WHERE id != 'grid'")}
    assert all(abs(n["alt_m"] - dem[n["id"]]) < 1 for n in db.query("SELECT id, alt_m FROM nodes")), "DEM heights used"
    live, demo = world.weather("sector_x", "live"), world.weather("sector_x", "demo")
    assert "open_meteo_forecast" in set(live["source"]) and "open_meteo_forecast" not in set(demo["source"])
    assert live.index.is_unique and demo.index.is_unique
    s_live, s_demo = world.stock("live"), world.stock("demo")  # Live is earlier than the demo date
    assert (s_live["qty"].to_numpy() >= s_demo["qty"].to_numpy() - 1e-6).all()


if __name__ == "__main__":
    check_adapters()
    check_real_data()
    check_demo_story()
    print("selfcheck OK")
