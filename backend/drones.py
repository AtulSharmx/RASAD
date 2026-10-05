"""Step 6 (USP C): drone deployment advisor - "if N drones of altitude band X arrive, where should they be based?"

Candidate bases are staging points troops already hold and supply by road (roadheads and nodes); the base is
assumed stocked by road before its own route closes. For each candidate, the planner is re-run with the extra
drones, and the base is ranked by the money, helicopter sorties and porter/mule trips it saves this week.
"""
import functools

from backend import costs, db, planner

F = db.PARAMS["fleet"]


def kpis(plan: dict) -> dict:
    lines = plan["lines"]
    by = lambda mode: [l for l in lines if l["mode"] == mode]
    return {"cost_inr": plan["total_cost_inr"],
            "heli_sorties": sum(l["trips"] for l in by("helicopter")),
            "heli_hours": round(sum(l["heli_hours"] for l in by("helicopter")), 1),
            "drone_sorties": sum(l["trips"] for l in by("drone")),
            "foot_trips": sum(l["trips"] for l in by("mule") + by("porter")),
            "not_moved_kg": sum(l["kg"] for l in by("not moved")),
            "heli_by_post": {p: sum(l["trips"] for l in by("helicopter") if l["post_name"] == p)
                             for p in sorted({l["post_name"] for l in lines})}}


@functools.lru_cache(maxsize=8)
def advise(mode: str = "demo", n: int = 20, band: str = "12000_20000ft") -> dict:
    existing = F["drones_at"]["v"]
    before = kpis(planner.run(mode))
    nodes = {r["id"]: r["name"] for r in db.query("SELECT id, name FROM nodes WHERE kind IN ('roadhead', 'node')")}
    rows = []
    for base_id, name in nodes.items():
        p = planner.plan(mode, drones_at={**existing, base_id: existing.get(base_id, 0) + n}, drone_band=band)
        k = kpis(p)
        served = sorted({l["post_name"] for l in p["lines"] if l["mode"] == "drone" and l["from"] == name})
        rows.append({"base": base_id, "base_name": name, "after": k, "posts_served": served,
                     "saved_inr": before["cost_inr"] - k["cost_inr"],
                     "heli_sorties_saved": before["heli_sorties"] - k["heli_sorties"],
                     "heli_hours_saved": round(before["heli_hours"] - k["heli_hours"], 1),
                     "foot_trips_saved": before["foot_trips"] - k["foot_trips"],
                     "not_moved_kg_saved": before["not_moved_kg"] - k["not_moved_kg"]})
    rows.sort(key=lambda r: -r["saved_inr"])
    best = rows[0]
    label = {"up_to_6000ft": "up to 6,000 ft", "6000_12000ft": "6,000-12,000 ft",
             "12000_20000ft": "12,000-20,000 ft"}[band]
    fox_before = before["heli_by_post"].get("Post Foxtrot", 0)
    fox_after = best["after"]["heli_by_post"].get("Post Foxtrot", 0)
    if best["saved_inr"] > 0:
        headline = (f"{n} drones ({label} band) at {best['base_name']}: helicopter sorties to Post Foxtrot drop from "
                    f"{fox_before} to {fox_after} this week, and Rs {best['saved_inr'] / 1e5:,.1f} lakh is saved "
                    f"({best['heli_hours_saved']} helicopter hours). Today Foxtrot is out of drone reach: the only "
                    f"drones are at Roadhead Lima, 19 km away (range 10 km). Cost inputs: truck "
                    f"Rs {costs.TRUCK}/kg-km and helicopter Rs {costs.HELI_HOUR:,}/h (The Week 2020); PLACEHOLDER.")
    else:
        headline = f"{n} drones of the {label} band save nothing this week: no base can reach the posts in need."
    return {"n": n, "band": band, "headline": headline, "before": before, "ranking": rows,
            "foxtrot": {"heli_sorties_before": fox_before, "heli_sorties_after": fox_after,
                        "saved_inr": best["saved_inr"], "base": best["base_name"]},
            "assumption": "A drone base is stocked by road before its own route closes; drones fly only on days inside "
                          "the drone weather limits; capacity follows flight time, battery swap and recharge."}
