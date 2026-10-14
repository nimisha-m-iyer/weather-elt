"""Validate hourly weather rows. Pure functions: no network, no database."""

import json
import math
from datetime import date, datetime
from pathlib import Path

RAW_DIR = Path("data/raw")

TEMP_MIN, TEMP_MAX = -10.0, 55.0   # plausible range for India, in °C
FIELDS = ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m"]


def rows_from_raw(city, data):
    """Turn the API's columns (one list per field) into one dict per hour."""
    hourly = data["hourly"]
    rows = []
    for i, hour in enumerate(hourly["time"]):
        row = {"city": city, "hour": hour}
        for field in FIELDS:
            values = hourly.get(field, [])
            row[field] = values[i] if i < len(values) else None
        rows.append(row)
    return rows


def validate_row(row):
    """Return None if the row is good, or a reason string if it is bad."""
    hour = row.get("hour")
    if hour is None:
        return "missing hour"
    try:
        datetime.fromisoformat(hour)
    except (TypeError, ValueError):
        return f"invalid hour: {hour!r}"

    for field in FIELDS:
        value = row.get(field)
        if value is None:
            return f"missing value: {field}"
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"non-numeric value: {field}"
        if math.isnan(value):
            return f"NaN value: {field}"

    temp = row["temperature_2m"]
    if not TEMP_MIN <= temp <= TEMP_MAX:
        return f"temperature out of range: {temp}"
    if not 0 <= row["relative_humidity_2m"] <= 100:
        return f"humidity out of range: {row['relative_humidity_2m']}"
    if row["precipitation"] < 0:
        return f"negative precipitation: {row['precipitation']}"
    if row["wind_speed_10m"] < 0:
        return f"negative wind speed: {row['wind_speed_10m']}"
    return None


def validate_rows(rows):
    """Split rows into (valid, rejected). Each rejected row carries a 'reason'."""
    valid, rejected = [], []
    for row in rows:
        reason = validate_row(row)
        if reason is None:
            valid.append(row)
        else:
            rejected.append({**row, "reason": reason})
    return valid, rejected


def validate_day(day):
    """Read all saved raw files for a day and validate them."""
    folder = RAW_DIR / day.isoformat()
    if not folder.exists():
        raise FileNotFoundError(f"No raw data for {day}: run extract first")

    valid, rejected = [], []
    for path in sorted(folder.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        v, r = validate_rows(rows_from_raw(path.stem, data))
        valid.extend(v)
        rejected.extend(r)
    return valid, rejected


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Validate raw weather files.")
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    args = parser.parse_args()

    good, bad = validate_day(args.date)
    print(f"valid: {len(good)}  rejected: {len(bad)}")
    for row in bad[:10]:
        print(row["city"], row["hour"], "->", row["reason"])