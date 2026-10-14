"""Extract hourly weather for five Indian cities and save the raw JSON."""

import argparse
import json
import logging
import time
from datetime import date, timedelta
from pathlib import Path

import requests

CITIES = {
    "Kochi":     (9.9312, 76.2673),
    "Mumbai":    (19.0760, 72.8777),
    "Delhi":     (28.6139, 77.2090),
    "Chennai":   (13.0827, 80.2707),
    "Bengaluru": (12.9716, 77.5946),
}

URL = "https://api.open-meteo.com/v1/forecast"
HOURLY_FIELDS = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
RAW_DIR = Path("data/raw")

TIMEOUT_SECONDS = 30
MAX_RETRIES = 3
BACKOFF_SECONDS = 2  # wait 2s, then 4s, then give up

log = logging.getLogger(__name__)


def fetch_city(city, lat, lon, day):
    """Call the API for one city and one day. Retries on failure."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": HOURLY_FIELDS,
        "timezone": "Asia/Kolkata",
        "start_date": day.isoformat(),
        "end_date": day.isoformat(),
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(URL, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            log.warning("%s: attempt %d/%d failed: %s", city, attempt, MAX_RETRIES, err)
            if attempt == MAX_RETRIES:
                raise  # out of retries, let the caller know
            time.sleep(BACKOFF_SECONDS * 2 ** (attempt - 1))


def save_raw(city, day, data):
    """Write the untouched API response to data/raw/{date}/{city}.json."""
    folder = RAW_DIR / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{city}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def extract_day(day):
    """Fetch and save all cities. Returns the list of cities that failed."""
    failed = []
    for city, (lat, lon) in CITIES.items():
        try:
            data = fetch_city(city, lat, lon, day)
            path = save_raw(city, day, data)
            log.info("%s: saved %s", city, path)
        except requests.exceptions.RequestException:
            log.error("%s: giving up after %d attempts", city, MAX_RETRIES)
            failed.append(city)
    return failed


def parse_args():
    parser = argparse.ArgumentParser(description="Extract raw weather data.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=date.today() - timedelta(days=1),
        help="Day to extract as YYYY-MM-DD (default: yesterday)",
    )
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args()
    log.info("Extracting weather for %s", args.date)

    failed = extract_day(args.date)
    if failed:
        raise SystemExit(f"Extraction failed for: {', '.join(failed)}")
    log.info("Done: %d cities saved", len(CITIES))


if __name__ == "__main__":
    main()