"""Load validated weather rows into PostgreSQL (idempotent)."""

import argparse
import json
import logging
import math
import os
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

from src.validate import validate_day

SCHEMA_FILE = Path("sql/01_tables.sql")

log = logging.getLogger(__name__)

COLUMNS = ["city", "hour", "temperature_2m", "relative_humidity_2m",
           "precipitation", "wind_speed_10m"]


def get_connection():
    """Connect using environment variables, with local-dev defaults."""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        user=os.getenv("PGUSER", "weather"),
        password=os.getenv("PGPASSWORD", "weather123"),
        dbname=os.getenv("PGDATABASE", "weather"),
    )


def init_schema(cur):
    """Create tables if they don't exist yet."""
    cur.execute(SCHEMA_FILE.read_text(encoding="utf-8"))


def to_json(row):
    """Turn a rejected row into JSON text. NaN is not valid JSON, so use null."""
    clean = {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in row.items()
        if k != "reason"
    }
    return json.dumps(clean, default=str)


def upsert_valid(cur, rows):
    """Insert rows, or update them if (city, hour) already exists."""
    if not rows:
        return
    values = [tuple(r[c] for c in COLUMNS) for r in rows]
    execute_values(
        cur,
        """
        INSERT INTO weather_hourly (city, hour, temperature_2m,
                                    relative_humidity_2m, precipitation, wind_speed_10m)
        VALUES %s
        ON CONFLICT (city, hour) DO UPDATE SET
            temperature_2m       = EXCLUDED.temperature_2m,
            relative_humidity_2m = EXCLUDED.relative_humidity_2m,
            precipitation        = EXCLUDED.precipitation,
            wind_speed_10m       = EXCLUDED.wind_speed_10m,
            loaded_at            = now()
        """,
        values,
    )


def replace_rejected(cur, day, rows):
    """Delete this day's rejected rows, then insert the current ones."""
    cur.execute("DELETE FROM rejected_rows WHERE data_date = %s", (day,))
    if not rows:
        return
    values = [(day, r.get("city"), r.get("hour"), r["reason"], to_json(r)) for r in rows]
    execute_values(
        cur,
        "INSERT INTO rejected_rows (data_date, city, hour, reason, raw_row) VALUES %s",
        values,
    )


def load_day(day):
    """Validate a day's raw files and load them in one transaction."""
    valid, rejected = validate_day(day)

    conn = get_connection()
    try:
        with conn:                      # commit on success, roll back on any error
            with conn.cursor() as cur:
                init_schema(cur)
                upsert_valid(cur, valid)
                replace_rejected(cur, day, rejected)
    finally:
        conn.close()

    log.info("%s: upserted %d valid rows, %d rejected", day, len(valid), len(rejected))
    return len(valid), len(rejected)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Load a day of weather data.")
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    load_day(args.date)


if __name__ == "__main__":
    main()