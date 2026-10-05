"""Quick check of the core logic. Run after gen_data: python -m backend.selfcheck"""
import pandas as pd

from backend import adapters, db


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


if __name__ == "__main__":
    check_adapters()
    check_demo_story()
    print("selfcheck OK")
