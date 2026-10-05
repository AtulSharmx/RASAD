"""ONE place for every cost input (params.json -> "costs"). The Point of No Return, the planner, the
drone advisor and the what-ifs all price through these functions, so every rupee in the app has the
same basis. All rates are PLACEHOLDER: truck and helicopter are derived from one public report
(The Week, 2020); the others are made up.
"""
from backend import db

C, M = db.PARAMS["costs"], db.PARAMS["modes"]
TRUCK = C["truck_inr_per_kg_km"]["v"]  # = Rs 10/kg for the ~420 km Srinagar-Leh haul
JEEP = TRUCK * C["jeep_factor"]["v"]
HELI_HOUR = C["heli_inr_per_hour"]["v"]


def road(km_road: float, km_jeep: float = 0) -> float:
    """Rs per kg by truck, and by jeep on jeep tracks."""
    return km_road * TRUCK + km_jeep * JEEP


def foot_per_kg(kind: str, km_track: float) -> float:
    """Rs per kg carried by mule or porter along a track."""
    return km_track * C[f"{kind}_inr_per_trip_km"]["v"] / M[kind]["payload_kg"]["v"]


def foot_trip(kind: str, km_track: float, km_road: float = 0, km_jeep: float = 0) -> float:
    """Rs per mule/porter trip, including the ride of its load to the roadhead."""
    return (foot_per_kg(kind, km_track) + road(km_road, km_jeep)) * M[kind]["payload_kg"]["v"]


def heli_sortie(hours: float) -> float:
    return hours * HELI_HOUR


def drone_sortie(payload: float, km_road: float = 0, km_jeep: float = 0) -> float:
    """Rs per drone sortie, including the ride of its load to the drone base."""
    return C["drone_inr_per_sortie"]["v"] + road(km_road, km_jeep) * payload


def basis(road_per_kg: float, air_per_kg: float) -> str:
    """The inputs behind every cost multiple, shown next to it (never a bare 'x times')."""
    return (f"road Rs {road_per_kg:,.1f}/kg vs helicopter Rs {air_per_kg:,.0f}/kg; inputs: truck "
            f"Rs {TRUCK}/kg-km (= Rs 1 lakh per 10 t Srinagar-Leh), helicopter Rs {HELI_HOUR:,}/h "
            "(= Rs 4 lakh per 45-min sortie), The Week 2020; PLACEHOLDER")


INPUTS = {"source": C["source"], "tag": "PLACEHOLDER",
          "rates": {k: {"value": v["v"], "src": v["src"]} for k, v in C.items() if isinstance(v, dict)}}
