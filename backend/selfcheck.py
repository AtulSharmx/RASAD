"""Quick check of the core logic. Run after gen_data: python -m backend.selfcheck"""
import pandas as pd

import json

from backend import adapters, anomaly, closure, costs, db, drones, forecast, planner, scenarios, world


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


def check_forecast():
    r = forecast.run("demo")
    acc = r["accuracy"].set_index("class")
    assert acc.loc["kerosene", "method"] == "LightGBM model", acc
    assert (acc["select_to"] < acc["test_from"]).all(), "method chosen only on the earlier window"
    assert acc["coverage_pct"].between(70, 90).all(), acc["coverage_pct"]
    c = r["cover"].set_index(["post", "class"])
    assert c.loc[("PA", "kerosene"), "status"] == "red" and c.loc[("PD", "medical"), "status"] == "red"
    assert sorted(set(c[c["status"] != "green"].index.get_level_values(0))) == ["PA", "PD", "PF"], "3 posts at risk"
    assert ((c["days_low"] <= c["days"]) & (c["days"] <= c["days_high"])).all()
    more_troops = forecast.cover("demo", forecast.forecast("demo", {"PF": 1.2})).set_index(["post", "class"])
    assert more_troops.loc[("PF", "rations"), "days"] < c.loc[("PF", "rations"), "days"], "troops +20% => less cover"
    assert len(forecast.run("live")["cover"]) == 40


def check_pnr():
    r = closure.run("demo")
    for a in r["axes"]:
        assert a["rule"]["loo_error_days"] < 25, a["rule"]
    assert "2026-11-01" <= r["axes"][1]["closure_p50"] <= "2026-11-30", "Manali-Leh usually closes in November"
    items = {(i["post"], i["class"]): i for i in r["items"]}
    pa = items[("PA", "kerosene")]
    assert pa["status"] == "urgent" and 0 <= pa["days_left"] <= 7 and pa["cost_multiple"] > 1, pa
    assert items[("PD", "medical")]["status"] == "passed", "Delta's track is closed: air only"
    assert items[("PF", "rations")]["status"] in ("urgent", "passed")
    assert sorted({i["post"] for i in r["items"] if i["status"] in ("passed", "urgent")}) == ["PA", "PD", "PF"]
    for c in r["curves"].values():
        p = [x["p_closed"] for x in c]
        assert p == sorted(p), "closure probability can only grow with time"


def check_plan():
    r = planner.run("demo")
    lines = r["lines"]
    assert lines and all(l["reason"] and l["cost_inr"] >= 0 for l in lines)
    for l in lines:
        if l["mode"] in ("truck", "jeep", "mule", "porter"):  # ground leaves before the Point of No Return
            assert max(l["days"]) <= l["last_safe_dispatch"], l
        if l["mode"] in ("mule", "porter", "helicopter"):
            assert any(a["tag"].startswith("PLACEHOLDER") for a in l["assumptions"]), l
    drone = [l for l in lines if l["post"] == "PD" and l["mode"] == "drone"]
    assert drone and drone[0]["kg"] <= 15 * drone[0]["trips"], "Delta's medicine goes by drone, 15 kg per sortie"
    assert any(l["post"] == "PF" and l["mode"] == "helicopter" for l in lines)
    assert sorted({l["post"] for l in lines}) == ["PA", "PD", "PF"]
    # commander in the loop: QM cannot approve; commander can; both leave an audit trail
    key = drone[0]["key"]
    try:
        planner.decide("demo", key, "approve", "Post QM", "selfcheck")
        raise AssertionError("Post QM must not approve")
    except PermissionError:
        pass
    planner.decide("demo", key, "approve", "Commander", "selfcheck", note="test")
    assert planner.with_decisions(r)["lines"][lines.index(drone[0])]["status"] == "approved"
    assert db.query("SELECT COUNT(*) n FROM audit_log WHERE user = 'selfcheck'")[0]["n"] == 1
    with db.connect() as con:  # leave the demo clean
        con.execute("DELETE FROM decisions WHERE user = 'selfcheck'")
        con.execute("DELETE FROM audit_log WHERE user = 'selfcheck'")


def check_step6():
    # one set of cost inputs: the PNR road cost for Alpha is exactly the shared rate x its route
    pa = next(i for i in closure.run("demo")["items"] if i["post"] == "PA" and i["class"] == "kerosene")
    assert abs(pa["road_inr_per_kg"] - round(costs.road(80, 20), 1)) < 0.11, pa["road_inr_per_kg"]
    # drones respect flight time, batteries and the drones available
    d = next(l for l in planner.run("demo")["lines"] if l["post"] == "PD" and l["mode"] == "drone")
    for day in d["schedule"]:
        assert day["trips"] <= 4 * (8 * 60 // 55), day  # 4 drones, one sortie per ~55-min cycle
    a = drones.advise("demo")
    assert a["ranking"][0]["base_name"] == "Node Mike" and "Post Foxtrot" in a["ranking"][0]["posts_served"]
    assert a["foxtrot"]["heli_sorties_after"] < a["foxtrot"]["heli_sorties_before"] and a["foxtrot"]["saved_inr"] > 0
    runs = {r["id"]: r for r in scenarios.all_runs("demo")}
    assert runs["pass_early"]["after"]["posts_at_risk"] >= runs["pass_early"]["before"]["posts_at_risk"]
    assert runs["pass_early"]["after"]["heli_sorties"] > runs["pass_early"]["before"]["heli_sorties"]
    assert runs["blizzard"]["after"]["heli_sorties"] <= runs["blizzard"]["before"]["heli_sorties"]
    assert runs["troops"]["after"]["posts_at_risk"] > runs["troops"]["before"]["posts_at_risk"]
    assert runs["drones"]["after"]["cost_inr"] < runs["drones"]["before"]["cost_inr"]


def check_alerts():
    found = {(a["post"], a["class"]): a for a in anomaly.run("demo")}
    kinds = {"data entry error": "data error", "possible pilferage": "steady excess", "genuine surge": "sharp surge"}
    for t in json.loads((db.ROOT / "data" / "anomaly_truth.json").read_text()):
        a = found.get((t["post"], t["class"]))
        assert a and a["kind"] == kinds[t["kind"]] and a["start"] <= t["end"] and a["end"] >= t["start"], (t, a)
    assert found[("PH", "kerosene")]["kind"] in ("silent sensor", "steady excess")
    assert any(a["kind"] == "silent sensor" and a["post"] == "PH" for a in anomaly.run("demo")), "Hotel's silent sensor"
    assert len(anomaly.run("demo")) <= 6, "few false alarms"
    for a in anomaly.run("demo"):  # never worded as a confirmed accusation
        assert a["plain"].startswith("Possible ") and "verify on ground" in a["plain"], a["plain"]


if __name__ == "__main__":
    check_adapters()
    check_forecast()
    check_real_data()
    check_demo_story()
    check_pnr()
    check_plan()
    check_step6()
    check_alerts()
    print("selfcheck OK")
