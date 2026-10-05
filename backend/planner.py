"""Step 5 (USP A): mixed-fleet last-mile planner.

For the next 7 days, decide which mode carries which load: truck/jeep, mule, porter, helicopter or drone.
Google OR-Tools CP-SAT chooses whole trips/sorties per load, mode and day to keep cost low while moving
urgent loads first. Hard rules:
- road, mule and porter loads leave on or before the Point of No Return date (Step 4), and never on a closed route;
- payload and range limits per mode; drones carry 15 kg in the 12,000-20,000 ft band and must clear the terrain;
- weather: helicopters and drones fly only on days inside their limits; helicopter hours come from the airlift allotment;
- fleet sizes per roadhead (mules, porters, jeeps, trucks, drones).
Every line gets a plain reason, its cost and the assumptions behind it (with PLACEHOLDER tags).
"""
import functools
import json
import math

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from backend import closure, costs, db, forecast, world

P = db.PARAMS
M, F, PL = P["modes"], P["fleet"], P["planner"]
DAY = pd.Timedelta(days=1)


def _tag(x: dict) -> str:
    return "PLACEHOLDER" if x["src"].startswith(("PLACEHOLDER", "DERIVED")) else "public source"


def _leg_top(a: dict, b: dict, grid: pd.DataFrame) -> float:
    """Highest real terrain (Copernicus DEM grid) within ~1 km of the straight leg, plus the end points."""
    t = np.linspace(0, 1, 30)
    lat, lon = a["lat"] + t * (b["lat"] - a["lat"]), a["lon"] + t * (b["lon"] - a["lon"])
    d = np.hypot((grid["lat"].to_numpy()[:, None] - lat) * 111, (grid["lon"].to_numpy()[:, None] - lon) * 92)
    near = grid["elev_m"].to_numpy()[(d < 1.0).any(axis=1)]
    return float(max([a["alt_m"], b["alt_m"], *near]))


def _flyable(mode: str, days: list, grounded: int) -> dict:
    w = world.weather("sector_x", mode)
    out = {}
    for i, d in enumerate(days):
        r = w.loc[d.date().isoformat()]
        h, dr = M["helicopter"], M["drone"]
        out[d] = {
            "heli": bool(i >= grounded and r["gust_max_kmh"] <= h["max_wind_kmh"]["v"]
                         and r["snowfall_cm"] <= h["max_snowfall_cm"]["v"] and r["cloud_pct"] <= h["max_cloud_pct"]["v"]),
            "drone": bool(r["gust_max_kmh"] <= dr["max_wind_kmh"]["v"] and r["snowfall_cm"] <= dr["max_snowfall_cm"]["v"]),
            "wx": f"gust {r['gust_max_kmh']:.0f} km/h, snow {r['snowfall_cm']:.1f} cm, cloud {r['cloud_pct']:.0f}%"}
    return out


CEILING_M = {"up_to_6000ft": 1829, "6000_12000ft": 3658, "12000_20000ft": 6096}  # top of each RFI band


def _supply(node_id: str, links: dict) -> tuple[float, float]:
    """(road km, jeep-track km) from the depot to a node: what its loads ride before the last leg."""
    km = {"road": 0.0, "jeep_track": 0.0, "mule_track": 0.0}
    while node_id in links:
        km[links[node_id]["mode"]] += links[node_id]["km"]
        node_id = links[node_id]["from_node"]
    return km["road"], km["jeep_track"]


def plan(mode: str = "demo", pnr: dict | None = None, drones_at: dict | None = None, grounded_days: int = 0,
         drone_band: str = "12000_20000ft") -> dict:
    """pnr / drones_at / grounded_days / drone_band let the advisor and what-ifs change the inputs."""
    pnr = pnr or closure.run(mode)
    drones_at = F["drones_at"]["v"] if drones_at is None else drones_at
    now = world.clock(mode).normalize()
    H = PL["horizon_days"]["v"]
    days = [now + i * DAY for i in range(H)]
    nodes = {n["id"]: n for n in db.query("SELECT * FROM nodes")}
    links = {l["to_node"]: l for l in db.query("SELECT * FROM links")}
    grid = pd.DataFrame(db.query("SELECT lat, lon, elev_m FROM terrain WHERE id = 'grid'"))
    hours = {r["date"]: r["h"] for r in db.query("SELECT date, SUM(hours) h FROM airlift GROUP BY date")}
    fly = _flyable(mode, days, grounded_days)
    cover = forecast.run(mode)["cover"].set_index(["post", "class"])["days"]
    season0 = closure._season_start(now)
    loads = [dict(i) for i in pnr["items"] if i["status"] in ("passed", "urgent") and i["shortfall_kg"] > 0]

    m = cp_model.CpModel()
    opts = []  # one entry per (load, option, day)
    use = {"mules": {}, "porters": {}, "jeeps": [], "trucks": [], "heli": [], "drone": {}}
    for li, ld in enumerate(loads):
        post = nodes[ld["post"]]
        last = links[ld["post"]]
        rh = nodes[last["from_node"]]
        to_rh = links[rh["id"]]
        open_route = all(r["status"] != "closed" for r in db.query(
            "SELECT status FROM road_status WHERE segment IN (?, ?)", (last["id"], to_rh["id"])))
        last_safe = pd.Timestamp(ld["last_safe_dispatch"])
        cand = []
        if open_route:  # ground options, only up to the Point of No Return
            ground_days = [d for d in days if d <= last_safe]
            if last["mode"] in ("road", "jeep_track"):
                jeep = last["mode"] == "jeep_track"
                cand.append(("jeep" if jeep else "truck", rh["id"], ground_days,
                             M["truck"]["jeep_payload_kg" if jeep else "payload_kg"]["v"], 0, ld["road_inr_per_kg"], 1))
            for animal in ("mule", "porter"):
                if last["mode"] != "road":
                    rt = math.ceil(2 * last["km"] / M[animal]["speed_kmh"]["v"] / M["truck"]["drive_hours_per_day"]["v"])
                    trip = costs.foot_trip(animal, last["km"], *_supply(rh["id"], links))
                    cand.append((animal, rh["id"], ground_days, M[animal]["payload_kg"]["v"], trip, 0, rt))
        # helicopter from Leh to the post's helipad (or the nearest one + porters)
        pads = [n for n in nodes.values() if n["helipad"] and n["kind"] != "depot"]
        pad = post if post["helipad"] else min(pads, key=lambda n: closure._dist_km(n, post))
        curve = np.array(M["helicopter"]["payload_kg_by_alt_m"]["v"])
        hp = float(np.interp(pad["alt_m"], curve[:, 0], curve[:, 1]))
        sortie_h = 2 * closure._dist_km(nodes["LEH"], pad) / M["helicopter"]["speed_kmh"]["v"] + M["helicopter"]["handling_hours"]["v"]
        foot = 0 if pad is post else costs.foot_per_kg("porter", closure._dist_km(pad, post) * 1.4)
        cand.append(("helicopter", pad["id"], [d for d in days if fly[d]["heli"]], round(hp),
                     costs.heli_sortie(sortie_h), foot, sortie_h))
        # drones from every base that holds drones, if in range and able to clear the terrain
        drone_note = []
        for base_id, n_drones in drones_at.items():
            base = nodes[base_id]
            dist = closure._dist_km(base, post)
            top = _leg_top(base, post, grid) + M["drone"]["clearance_m"]["v"]
            if dist > M["drone"]["range_km_one_way"]["v"]:
                drone_note.append(f"drones at {base['name']} are {dist:.0f} km away (range {M['drone']['range_km_one_way']['v']} km)")
                continue
            if top > CEILING_M[drone_band]:
                drone_note.append(f"the leg from {base['name']} must clear {top:,.0f} m, above the "
                                  f"{drone_band.replace('_', ' ')} drone band")
                continue
            dr = M["drone"]
            flight = 2 * dist / dr["speed_kmh"]["v"] * 60  # minutes in the air, there and back
            if flight > dr["endurance_min"]["v"]:
                drone_note.append(f"a round trip from {base['name']} takes {flight:.0f} min, beyond the battery's "
                                  f"{dr['endurance_min']['v']} min")
                continue
            # one sortie ties up a drone for flight + swap, and a battery for flight + recharge (shared by B batteries)
            cycle = max(flight + dr["swap_min"]["v"], (flight + dr["charge_min"]["v"]) / dr["batteries_per_drone"]["v"])
            pay = M["drone"]["payload_kg_by_band"]["v"][drone_band]
            trip = costs.drone_sortie(pay, *_supply(base_id, links))
            cand.append(("drone", base_id, [d for d in days if fly[d]["drone"]], pay, trip, 0,
                         (n_drones, dist, top, flight, cycle)))
        if not drones_at:
            drone_note.append("no drones held in the sector")
        ld["_drone_note"] = drone_note
        ld["_pad"], ld["_heli_payload"] = pad, hp
        # create variables
        run_out = cover.get((ld["post"], ld["class"]), H)
        pen = PL["undelivered_inr_per_kg"]["v"][ld["class"]]
        dw = PL["delay_inr_per_kg_day"]["v"][ld["class"]]
        qty = int(ld["shortfall_kg"])
        ld["_kg_vars"] = []
        for kind, src, ok_days, pay, trip_cost, kg_cost, extra in cand:
            for d in ok_days:
                i = (d - now).days
                trips = m.new_int_var(0, math.ceil(qty / pay), f"t{li}_{kind}_{src}_{i}")
                kg = m.new_int_var(0, qty, f"k{li}_{kind}_{src}_{i}")
                m.add(kg <= trips * int(pay))
                delay = dw * i * (10 if i >= run_out else 1)
                opts.append({"load": li, "kind": kind, "src": src, "day": d, "trips": trips, "kg": kg,
                             "cost": (trip_cost, kg_cost), "delay": delay, "pay": pay, "extra": extra})
                ld["_kg_vars"].append(kg)
                if kind in ("mule", "porter"):
                    use[kind + "s"].setdefault(src, []).append((trips, extra, i))
                elif kind == "jeep":
                    use["jeeps"].append((trips, i))
                elif kind == "helicopter":
                    use["heli"].append((trips, extra, d))
                else:
                    use["drone"].setdefault(src, []).append((trips, extra, d))
                if kind != "helicopter":  # everything else leaves from a roadhead, so it rides a truck first
                    use["trucks"].append((kg, i))
        ld["_short"] = m.new_int_var(0, qty, f"u{li}")
        m.add(sum(ld["_kg_vars"]) + ld["_short"] == qty)
        ld["_pen"] = pen

    # fleet limits
    for i in range(H):
        trips_jeep = [t for t, d in use["jeeps"] if d == i]
        if trips_jeep:
            m.add(sum(trips_jeep) <= F["jeeps"]["v"])
        kg_truck = [k for k, d in use["trucks"] if d == i]
        if kg_truck:  # ponytail: one round trip per truck per day to the roadheads
            m.add(sum(kg_truck) <= F["trucks"]["v"] * M["truck"]["payload_kg"]["v"])
    for kind, fleet in (("mules", F["mules_at"]["v"]), ("porters", F["porters_at"]["v"])):
        for src, rows in use[kind].items():
            n = fleet.get(src, 0)
            # ponytail: a trip ties an animal/porter up for its round-trip days; checked as a weekly total
            m.add(sum(t * rt for t, rt, _ in rows) <= n * H)
            for i in range(H):
                today = [t for t, _, d in rows if d == i]
                if today:
                    m.add(sum(today) <= n)
    for d in days:
        today = [t * round(100 * h) for t, h, dd in use["heli"] if dd == d]
        if today:
            m.add(sum(today) <= round(100 * hours.get(d.date().isoformat(), 0)))
    for src, rows in use["drone"].items():
        n_drones = rows[0][1][0]
        for d in days:
            today = [(t, x[4]) for t, x, dd in rows if dd == d]
            if today:  # each base's drones have op_hours of flying per day; a sortie uses one 'cycle' of it
                m.add(sum(t * round(c) for t, c in today) <= n_drones * M["drone"]["op_hours_per_day"]["v"] * 60)

    ten = lambda x: round(10 * x)  # CP-SAT needs whole numbers: work in tenths of a rupee
    cost = sum(ten(o["cost"][0]) * o["trips"] + ten(o["cost"][1] + o["delay"]) * o["kg"] for o in opts)
    m.minimize(cost + sum(ten(ld["_pen"]) * ld["_short"] for ld in loads))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20
    solver.parameters.num_workers = 1  # same answer every run
    solver.parameters.random_seed = 42
    status = solver.solve(m)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("planner found no plan")

    lines = []
    for li, ld in enumerate(loads):
        mine = [o for o in opts if o["load"] == li and solver.value(o["kg"]) > 0]
        groups = {}
        for o in mine:
            groups.setdefault((o["kind"], o["src"]), []).append(o)
        for (kind, src), os_ in groups.items():
            kg = sum(solver.value(o["kg"]) for o in os_)
            trips = sum(solver.value(o["trips"]) for o in os_)
            cost_inr = sum(o["cost"][0] * solver.value(o["trips"]) + o["cost"][1] * solver.value(o["kg"]) for o in os_)
            ds = sorted({o["day"] for o in os_})
            sched = [(o["day"], solver.value(o["trips"]), solver.value(o["kg"])) for o in os_ if solver.value(o["kg"])]
            lines.append(_line(mode, ld, kind, src, kg, trips, cost_inr, ds, os_[0], nodes, sched))
        short = solver.value(ld["_short"])
        if short > 0:
            lines.append(_line(mode, ld, "not moved", "", short, 0, 0, [], None, nodes))
    watch = [i for i in pnr["items"] if i["status"] == "watch"]
    return {"lines": lines, "horizon": [d.date().isoformat() for d in days],
            "weather": {d.date().isoformat(): fly[d] for d in days},
            "heli_hours_allotted": {d.date().isoformat(): hours.get(d.date().isoformat(), 0) for d in days},
            "total_cost_inr": round(sum(l["cost_inr"] for l in lines)),
            "watch": [{"post": w["post_name"], "class": w["label"], "last_safe_dispatch": w["last_safe_dispatch"]} for w in watch],
            "solver": solver.status_name(status)}


def _line(mode, ld, kind, src, kg, trips, cost_inr, ds, o, nodes, sched=()) -> dict:
    first, last_d = (ds[0], ds[-1]) if ds else (None, None)
    cls = P["classes"][ld["class"]]
    units = kg / cls["kg_per_unit"]
    qty_txt = f"{units:,.0f} {cls['unit']}" + (f" ({kg:,.0f} kg)" if cls["unit"] != "kg" else "")
    when = "" if first is None else (f"{first:%d %b}" if first == last_d else f"{first:%d}-{last_d:%d %b}")
    post = ld["post_name"]
    heli_per_kg = ld["air_inr_per_kg"]
    per_kg = cost_inr / kg if kg else 0
    h, dr = M["helicopter"], M["drone"]
    assumptions = []
    if kind in ("truck", "jeep"):
        reason = (f"Road open until {pd.Timestamp(ld['closure_p20']):%d %b} (80% confidence), so it leaves by "
                  f"{pd.Timestamp(ld['last_safe_dispatch']):%d %b}. By road ~Rs {per_kg:,.1f}/kg; a helicopter would be "
                  f"~Rs {heli_per_kg:,.0f}/kg (~{heli_per_kg / max(per_kg, 0.01):.0f}x).")
        assumptions = [("truck cost", f"Rs {costs.TRUCK}/kg-km (jeep x{costs.C['jeep_factor']['v']})", "PLACEHOLDER (The Week 2020)"),
                       (f"{kind} payload", f"{o['pay']:,.0f} kg", "PLACEHOLDER")]
    elif kind in ("mule", "porter"):
        reason = (f"{trips} {kind} trip{'s' if trips != 1 else ''} from {nodes[src]['name']} before the track closes "
                  f"({pd.Timestamp(ld['last_safe_dispatch']):%d %b} is the last safe day). ~Rs {per_kg:,.0f}/kg vs "
                  f"helicopter ~Rs {heli_per_kg:,.0f}/kg.")
        fleet = F["mules_at" if kind == "mule" else "porters_at"]["v"].get(src, 0)
        assumptions = [(f"{kind} load", f"{o['pay']} kg", _tag(M[kind]["payload_kg"]) + " (" + M[kind]["payload_kg"]["src"] + ")"),
                       (f"{kind}s at {nodes[src]['name']}", str(fleet), "PLACEHOLDER"),
                       (f"{kind} cost", f"Rs {costs.C[kind + '_inr_per_trip_km']['v']}/trip-km", "PLACEHOLDER")]
    elif kind == "helicopter":
        why_not_ground = ("the ground route is closed" if ld["status"] == "passed"
                          else f"the ground route closes by {pd.Timestamp(ld['last_safe_dispatch']):%d %b}")
        why_not_drone = "; ".join(ld["_drone_note"]) or "drones are busy or grounded"
        reason = (f"{trips} sorties to {nodes[src]['name']} on flyable days: {why_not_ground}; {why_not_drone}. "
                  f"~Rs {per_kg:,.0f}/kg ({costs.basis(ld['road_inr_per_kg'], per_kg)}).")
        assumptions = [("helicopter payload here", f"{o['pay']} kg", "PLACEHOLDER (altitude curve)"),
                       ("helicopter cost", f"Rs {costs.HELI_HOUR:,}/h", "PLACEHOLDER (The Week 2020)"),
                       ("helicopter hours per day", f"{F['heli_hours_per_day']['v']}", "PLACEHOLDER")]
    elif kind == "drone":
        n_drones, dist, top, flight, cycle = o["extra"]
        why = "track closed by snow" if ld["status"] == "passed" else "fast and cheap for small urgent loads"
        days_txt = "; ".join(
            f"{d:%d %b}: {s} sorties = {min(n_drones, s)} drones x up to {math.ceil(s / min(n_drones, s))} sorties, "
            f"{s} battery charges" for d, s, _ in sched)
        reason = (f"{trips} drone sorties from {nodes[src]['name']} ({dist:.1f} km, in the {dr['range_km_one_way']['v']} km range; "
                  f"leg clears {top:,.0f} m, so {o['pay']:.0f} kg per sortie): {why}. {days_txt}. Each sortie flies "
                  f"{flight:.0f} min; a drone can fly one every {cycle:.0f} min ({dr['batteries_per_drone']['v']} batteries, "
                  f"{dr['charge_min']['v']} min to recharge, {dr['swap_min']['v']} min swap). "
                  f"~Rs {per_kg:,.0f}/kg; helicopter would be ~Rs {heli_per_kg:,.0f}/kg (~{heli_per_kg / max(per_kg, 1):.0f}x).")
        assumptions = [("drone payload", f"{o['pay']:.0f} kg", "public source (Army RFP, Tribune Oct 2022)"),
                       ("drone range", f"{dr['range_km_one_way']['v']} km", "public source (RFIs)"),
                       ("drones held", f"{n_drones}", "PLACEHOLDER"),
                       ("drone cost", f"Rs {costs.C['drone_inr_per_sortie']['v']:,}/sortie", "PLACEHOLDER"),
                       ("batteries per drone / recharge", f"{dr['batteries_per_drone']['v']} / {dr['charge_min']['v']} min", "PLACEHOLDER"),
                       ("drone wind limit", f"{dr['max_wind_kmh']['v']} km/h", "PLACEHOLDER")]
    else:
        reason = ("Cannot be moved this week within the limits (helicopter hours, weather windows, fleet). "
                  "Needs a commander decision: more air effort, rationing or a later window.")
    key = f"{mode}:{ld['post']}:{ld['class']}:{kind}:{src}"
    return {"key": key, "post": ld["post"], "post_name": post, "class": ld["class"], "label": cls["label"],
            "mode": kind, "from": nodes[src]["name"] if src else "", "kg": int(kg), "qty_text": qty_txt,
            "trips": int(trips), "when": when, "days": [d.date().isoformat() for d in ds],
            "schedule": [{"date": d.date().isoformat(), "trips": int(s), "kg": int(k)} for d, s, k in sched],
            "heli_hours": round(trips * o["extra"], 1) if kind == "helicopter" else 0,
            "last_safe_dispatch": ld["last_safe_dispatch"], "cost_inr": round(cost_inr),
            "summary": f"{cls['label']} to {post} by {kind}: {qty_txt}" + (f", {when}" if when else ""),
            "reason": reason, "assumptions": [{"name": a, "value": v, "tag": t} for a, v, t in assumptions],
            "priority": "urgent" if ld["status"] in ("passed", "urgent") else "normal"}


@functools.lru_cache(maxsize=4)
def run(mode: str = "demo") -> dict:
    """The solved plan for a mode (cached; decisions are attached fresh by with_decisions)."""
    return plan(mode)


def with_decisions(result: dict) -> dict:
    dec = {r["key"]: r for r in db.query("SELECT * FROM decisions")}
    lines = [{**l, "status": dec[l["key"]]["status"] if l["key"] in dec else "pending",
              "decided_kg": dec[l["key"]]["kg"] if l["key"] in dec else None,
              "decision_note": dec[l["key"]]["note"] if l["key"] in dec else None} for l in result["lines"]]
    return {**result, "lines": lines}


ROLES = {"approve": {"Commander"}, "reject": {"Commander"}, "modify": {"Commander", "Logistics Officer"}}


def decide(mode: str, key: str, action: str, role: str, user: str, kg: float | None = None, note: str = "") -> dict:
    """Commander in the loop: approve / modify / reject one plan line. Every change goes to the audit log."""
    if action not in ROLES:
        raise ValueError("action must be approve, modify or reject")
    if role not in ROLES[action]:
        raise PermissionError(f"{role} cannot {action} (allowed: {', '.join(sorted(ROLES[action]))})")
    line = next((l for l in run(mode)["lines"] if l["key"] == key), None)
    if line is None:
        raise KeyError("no such plan line")
    if action == "modify" and (kg is None or not 0 <= kg <= 10 * line["kg"]):
        raise ValueError("modify needs a quantity in kg between 0 and 10x the planned amount")
    old = db.query("SELECT status, kg, note FROM decisions WHERE key = ?", (key,))
    before = old[0] if old else {"status": "pending", "kg": line["kg"], "note": None}
    after = {"status": {"approve": "approved", "modify": "modified", "reject": "rejected"}[action],
             "kg": kg if action == "modify" else before["kg"] if before["status"] == "modified" else line["kg"],
             "note": note[:500]}  # approving a modified line keeps the modified quantity
    ts = pd.Timestamp.now().isoformat(timespec="seconds")
    with db.connect() as con:
        con.execute("INSERT OR REPLACE INTO decisions VALUES(?,?,?,?,?,?,?)",
                    (key, after["status"], after["kg"], after["note"], role, user, ts))
        con.execute("INSERT INTO audit_log(ts, role, user, action, item, before, after, note) VALUES(?,?,?,?,?,?,?,?)",
                    (ts, role, user, action, f"{line['summary']} [{key}]", json.dumps(before), json.dumps(after), note[:500]))
    return after
