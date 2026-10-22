"""
Live Weather + Demographics ETL pipeline
========================================
Extracts live weather (temperature, wind speed) for 50 global capital cities from the
Open-Meteo API and stores it for the downstream demographics merge.
"""

from __future__ import annotations

import os
import sys
import time

import pandas as pd
import requests

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
POPULATION_CSV = os.path.join(DATA_DIR, "population.csv")

API_URL = "https://api.open-meteo.com/v1/forecast"


# --------------------------------------------------------------------------- #
# Step 3.1 - Extract: population dataset + live weather from Open-Meteo
# --------------------------------------------------------------------------- #
def load_population(path: str = POPULATION_CSV) -> pd.DataFrame:
    """Load the static demographic dataset."""
    if not os.path.exists(path):
        sys.exit(f"population.csv not found at {path}")
    df = pd.read_csv(path)
    print(f"[extract] loaded {len(df)} rows from {path}")
    return df


def fetch_weather(latitudes, longitudes, retries: int = 3, timeout: int = 30):
    """Call Open-Meteo for one or more locations and return the raw JSON payload.

    The API accepts comma-separated coordinates, so a single request can cover every
    capital city. It answers with a JSON array (one object per location).
    """
    params = {
        "latitude": ",".join(str(value) for value in latitudes),
        "longitude": ",".join(str(value) for value in longitudes),
        "current_weather": "true",
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(API_URL, params=params, timeout=timeout)
            response.raise_for_status()
            payload = response.json()
            return payload if isinstance(payload, list) else [payload]
        except (requests.RequestException, ValueError) as exc:
            if attempt == retries:
                print(f"  ! request failed: {exc}")
                return []
            time.sleep(attempt)
    return []


def collect_weather(population_df: pd.DataFrame) -> pd.DataFrame:
    """Fetch live weather for every location and return a tidy DataFrame."""
    latitudes = list(population_df["Latitude"])
    longitudes = list(population_df["Longitude"])
    print(f"[extract] requesting live weather for {len(latitudes)} cities ...", flush=True)
    payload = fetch_weather(latitudes, longitudes)

    records = []
    for row, location in zip(population_df.itertuples(index=False), payload):
        current = location.get("current_weather", {})
        records.append(
            {
                "City": row.City,
                "Country": row.Country,
                "Temperature": current.get("temperature"),
                "WindSpeed": current.get("windspeed"),
                "ObservedAt": current.get("time"),
            }
        )
        print(f"  {row.City:<16} temp={current.get('temperature')} wind={current.get('windspeed')}",
              flush=True)
    if len(payload) < len(latitudes):
        print(f"  ! received {len(payload)} of {len(latitudes)} locations", flush=True)
    return pd.DataFrame(records)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    population_df = load_population()
    weather_df = collect_weather(population_df)

    print("\n[extract] live weather preview:")
    print(weather_df.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
