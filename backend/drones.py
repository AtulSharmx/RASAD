"""Step 6 (USP C): drone deployment advisor - "if N drones of altitude band X arrive, where should they be based?"

Candidate bases are staging points troops already hold and supply by road (roadheads and nodes); the base is
assumed stocked by road before its own route closes. For each candidate, the planner is re-run with the extra
drones, and the base is ranked by the money, helicopter sorties and porter/mule trips it saves this week.
"""

from backend import cache, closure, costs, db, planner

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


def _reach(post_name: str | None, drones_at: dict) -> str:
    """Why the post is not served by drones today, measured from where drones are held now."""
    if not post_name:
        return ""
    nodes = {n["id"]: n for n in db.query("SELECT * FROM nodes")}
    post = next(n for n in nodes.values() if n["name"] == post_name)
    rng = db.PARAMS["modes"]["drone"]["range_km_one_way"]["v"]
    if not drones_at:
        return " Today no drones are held in the sector."
    km, base = min((closure._dist_km(nodes[b], post), nodes[b]["name"]) for b in drones_at)
    short = post_name.replace("Post ", "")
    return f" Today {short} is {km:.0f} km from the nearest drones ({base}), beyond their {rng} km range." if km > rng else ""


@cache.memo(maxsize=8)
def advise(mode: str = "demo", n: int = 20, band: str = "12000_20000ft") -> dict:
    existing = F["drones_at"]["v"]
    before = kpis(planner.run(mode))
    nodes = {r["id"]: r["name"] for r in db.query("SELECT id, name FROM nodes WHERE kind IN ('roadhead', 'node')")}
    rows = []
    for base_id, name in nodes.items():
        p = planner.plan(mode, drones_at={**existing, base_id: existing.get(base_id, 0) + n}, drone_band=band)
        k = kpis(p)
        served = sorted({l["post_name"] for l in p["lines"] if l["mode"] == "drone" and l["from"] == name})
        rows.append({"base": base_id, "base_name": name, "after": k, "posts_served": served, "solver": p["solver"],
                     "saved_inr": before["cost_inr"] - k["cost_inr"],
                     "heli_sorties_saved": before["heli_sorties"] - k["heli_sorties"],
                     "heli_hours_saved": round(before["heli_hours"] - k["heli_hours"], 1),
                     "foot_trips_saved": before["foot_trips"] - k["foot_trips"],
                     "not_moved_kg_saved": before["not_moved_kg"] - k["not_moved_kg"]})
    rows.sort(key=lambda r: -r["saved_inr"])
    best = rows[0]
    label = {"up_to_6000ft": "up to 6,000 ft", "6000_12000ft": "6,000-12,000 ft",
             "12000_20000ft": "12,000-20,000 ft"}[band]
    # the post whose helicopter sorties drop the most at the best base (none if no sortie is saved)
    hb, ha = before["heli_by_post"], best["after"]["heli_by_post"]
    focus = max(hb, key=lambda p: hb[p] - ha.get(p, 0), default=None)
    focus = focus if focus and hb[focus] > ha.get(focus, 0) else None
    f_before, f_after = (hb[focus], ha.get(focus, 0)) if focus else (0, 0)
    drones_txt = f"{n} drone{'' if n == 1 else 's'}"
    if best["saved_inr"] > 0:
        what = (f"helicopter sorties to {focus} drop from {f_before} to {f_after} this week, and " if focus else "")
        headline = (f"{drones_txt} ({label} band) at {best['base_name']}: {what}Rs {best['saved_inr'] / 1e5:,.1f} lakh "
                    f"is saved ({best['heli_hours_saved']} helicopter hours).{_reach(focus, existing)} Cost inputs: truck "
                    f"Rs {costs.TRUCK}/kg-km and helicopter Rs {costs.HELI_HOUR:,}/h (The Week 2020); PLACEHOLDER.")
    else:
        headline = f"{drones_txt} of the {label} band save nothing this week: no base can reach the posts in need."
    return {"n": n, "band": band, "headline": headline, "before": before, "ranking": rows,
            "focus": {"post": focus, "heli_sorties_before": f_before, "heli_sorties_after": f_after,
                      "saved_inr": best["saved_inr"], "base": best["base_name"]},
            "solver_limited": any(r["solver"] != "OPTIMAL" for r in rows) or planner.run(mode)["solver"] != "OPTIMAL",
            "assumption": "A drone base is stocked by road before its own route closes; drones fly only on days inside "
                          "the drone weather limits; capacity follows flight time, battery swap and recharge."}
