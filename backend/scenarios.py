"""Step 6 (USP E): one-click what-ifs. Each changes only the inputs, re-runs the Point of No Return and the
plan, and reports before vs after."""

from backend import cache, closure, db, drones, planner

TROOPS = (("PA", 1.2), ("PB", 1.2), ("PC", 1.2))
SCENARIOS = {
    "pass_early": "Pass closes 10 days early",
    "blizzard": "Blizzard grounds helicopters for 3 days",
    "troops": "Troop strength +20% at Posts Alpha-Charlie",
    "drones": "20 high-altitude drones arrive",
}


def _kpis(pnr: dict, plan: dict) -> dict:
    risk = sorted({i["post_name"] for i in pnr["items"] if i["status"] in ("passed", "urgent")})
    k = drones.kpis(plan)
    k.pop("heli_by_post")
    return {"posts_at_risk": len(risk), "at_risk": risk, **k}


@cache.memo(maxsize=16)
def run(mode: str, sid: str) -> dict:
    base_pnr, base_plan = closure.run(mode), planner.run(mode)
    pnr = base_pnr
    if sid == "pass_early":
        pnr = closure.run(mode, shift=-10)
        plan = planner.plan(mode, pnr=pnr)
    elif sid == "blizzard":
        plan = planner.plan(mode, grounded_days=3)
    elif sid == "troops":
        pnr = closure.run(mode, strength=TROOPS)
        plan = planner.plan(mode, pnr=pnr)
    elif sid == "drones":
        adv = drones.advise(mode)
        best = adv["ranking"][0]["base"]
        have = db.PARAMS["fleet"]["drones_at"]["v"]
        plan = planner.plan(mode, drones_at={**have, best: have.get(best, 0) + 20})
    else:
        raise KeyError(sid)
    before, after = _kpis(base_pnr, base_plan), _kpis(pnr, plan)
    names = {"posts_at_risk": "Posts at risk", "heli_sorties": "Helicopter sorties", "heli_hours": "Helicopter hours",
             "drone_sorties": "Drone sorties", "foot_trips": "Mule/porter trips", "not_moved_kg": "Not moved this week (kg)",
             "cost_inr": "Cost this week (Rs)"}
    changes = [f"{label}: {before[k]:,} -> {after[k]:,}" for k, label in names.items() if before[k] != after[k]]
    new_risk = sorted(set(after["at_risk"]) - set(before["at_risk"]))
    if new_risk:
        changes.insert(0, "New posts at risk: " + ", ".join(new_risk))
    if after["cost_inr"] < before["cost_inr"] and after["not_moved_kg"] > before["not_moved_kg"]:
        changes.append("Cost is lower only because some loads could not move this week (not a saving).")
    return {"id": sid, "title": SCENARIOS[sid], "before": before, "after": after, "changes": changes,
            "plan": plan["lines"]}


def all_runs(mode: str = "demo") -> list[dict]:
    return [run(mode, sid) for sid in SCENARIOS]
