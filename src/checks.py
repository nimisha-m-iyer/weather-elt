"""Post-load data quality checks. Any failure raises an error."""

import argparse
import logging
from datetime import date, datetime, time, timedelta, timezone

from src.extract import CITIES
from src.load import get_connection

EXPECTED_ROWS_PER_CITY = 24
MAX_REJECTED_RATIO = 0.05      # must be strictly below 5%
MAX_LOAD_AGE_HOURS = 24

log = logging.getLogger(__name__)


class DataQualityError(Exception):
    """Raised when one or more checks fail."""


# ---------- the three rules (pure: no database, easy to test) ----------

def check_row_counts(counts):
    """Every city must have exactly 24 rows for the day."""
    problems = []
    for city in CITIES:
        n = counts.get(city, 0)
        if n != EXPECTED_ROWS_PER_CITY:
            problems.append(f"{city}: expected {EXPECTED_ROWS_PER_CITY} rows, found {n}")
    return problems


def check_freshness(day, latest_hour, last_loaded_at, now):
    """The day must be complete (last hour is 23:00) and loaded recently."""
    if latest_hour is None:
        return [f"no rows found for {day}"]
    problems = []
    expected_last = datetime.combine(day, time(23, 0))
    if latest_hour < expected_last:
        problems.append(f"latest hour is {latest_hour}, expected {expected_last}")
    age = now - last_loaded_at
    if age > timedelta(hours=MAX_LOAD_AGE_HOURS):
        problems.append(f"last load was {age} ago (limit {MAX_LOAD_AGE_HOURS}h)")
    return problems


def check_rejected_ratio(valid, rejected):
    """Fewer than 5% of the day's rows may be rejected."""
    total = valid + rejected
    if total == 0:
        return ["no rows at all for this day"]
    ratio = rejected / total
    if ratio >= MAX_REJECTED_RATIO:
        return [f"{ratio:.1%} of rows rejected (limit {MAX_REJECTED_RATIO:.0%})"]
    return []


# ---------- database reading and the runner ----------

def fetch_stats(cur, day):
    cur.execute(
        "SELECT city, COUNT(*) FROM weather_hourly WHERE hour::date = %s GROUP BY city",
        (day,),
    )
    counts = {city: n for city, n in cur.fetchall()}
    cur.execute(
        "SELECT MAX(hour), MAX(loaded_at) FROM weather_hourly WHERE hour::date = %s",
        (day,),
    )
    latest_hour, last_loaded_at = cur.fetchone()
    cur.execute("SELECT COUNT(*) FROM rejected_rows WHERE data_date = %s", (day,))
    rejected = cur.fetchone()[0]
    return counts, latest_hour, last_loaded_at, rejected


def run_checks(day):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            counts, latest_hour, last_loaded_at, rejected = fetch_stats(cur, day)
    finally:
        conn.close()

    results = {
        "row_counts": check_row_counts(counts),
        "freshness": check_freshness(day, latest_hour, last_loaded_at,
                                     datetime.now(timezone.utc)),
        "rejected_ratio": check_rejected_ratio(sum(counts.values()), rejected),
    }

    failed = False
    for name, problems in results.items():
        if problems:
            failed = True
            for p in problems:
                log.error("FAIL %s: %s", name, p)
        else:
            log.info("PASS %s", name)

    if failed:
        raise DataQualityError(f"Quality checks failed for {day}")
    log.info("%s: all checks passed", day)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run data quality checks.")
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    try:
        run_checks(parser.parse_args().date)
    except DataQualityError as err:
        raise SystemExit(str(err))


if __name__ == "__main__":
    main()