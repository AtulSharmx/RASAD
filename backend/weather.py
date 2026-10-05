"""One-time download of REAL historical weather from Open-Meteo (ERA5), cached as CSV.

After this runs once, the app never needs the internet.
Data: Open-Meteo.com, CC BY 4.0 (attribution shown in the UI).
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
WEATHER_DIR = ROOT / "data" / "weather"

# Public places only. "sector_x" is just a weather grid point used for the fictional sector.
# (lat, lon, elevation override, start date). Passes and the sector need ~30 winters for the
# closure statistics; towns only need recent years (Open-Meteo's free limit is ~5,000 calls/hour).
LOCATIONS = {
    "leh": (34.1526, 77.5771, None, "1990-01-01"),
    "zojila": (34.2786, 75.4728, None, "1995-01-01"),
    "baralacha": (32.7583, 77.4247, None, "1995-01-01"),
    "tanglang": (33.5070, 77.7700, None, "1995-01-01"),
    "sector_x": (34.02, 76.80, 4000, "1995-01-01"),  # values are for 4,000 m; posts adjust by lapse rate
    "kargil": (34.5539, 76.1349, None, "2010-01-01"),
    "drass": (34.4317, 75.7543, None, "2010-01-01"),
}

UA = "RASAD-prototype/0.1 (SIH 2026 student project; offline cache)"


def fetch_json(url: str, data: bytes | None = None):
    """GET (or POST data) with polite retries when a free API says 'too many requests'."""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(60):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 504) or attempt == 59:
                raise
            print("    server busy / rate limited, waiting 70 s ...", flush=True)
            time.sleep(70)


DAILY = {  # Open-Meteo name -> our column
    "temperature_2m_max": "tmax",
    "temperature_2m_min": "tmin",
    "snowfall_sum": "snowfall_cm",
    "precipitation_sum": "precip_mm",
    "snow_depth_max": "snow_depth_m",
    "wind_speed_10m_max": "wind_max_kmh",
    "wind_gusts_10m_max": "gust_max_kmh",
    "cloud_cover_mean": "cloud_pct",
    "weather_code": "wcode",
}


def download(name: str, end: str) -> Path:
    lat, lon, elev, start = LOCATIONS[name]
    q = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "daily": ",".join(DAILY), "timezone": "Asia/Kolkata",
    }
    if elev is not None:
        q["elevation"] = elev
    d = fetch_json("https://archive-api.open-meteo.com/v1/archive?" + urllib.parse.urlencode(q))["daily"]
    df = pd.DataFrame(d).rename(columns={"time": "date", **DAILY})
    df = df.dropna(subset=["tmax", "tmin"])  # the last day or two can be empty
    df.insert(1, "location", name)
    out = WEATHER_DIR / f"{name}.csv"
    df.to_csv(out, index=False)
    return out


def ensure(force: bool = False) -> None:
    WEATHER_DIR.mkdir(parents=True, exist_ok=True)
    end = (date.today() - timedelta(days=1)).isoformat()
    for name, (*_, start) in LOCATIONS.items():
        if force or not (WEATHER_DIR / f"{name}.csv").exists():
            print(f"  downloading weather: {name} ({start} to {end}) ...", flush=True)
            download(name, end)


if __name__ == "__main__":
    ensure()
