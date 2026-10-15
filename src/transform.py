"""Build the staging view and refresh the daily summary for one day."""

import argparse
import logging
from datetime import date
from pathlib import Path

from src.load import get_connection

SQL_DIR = Path("sql")
log = logging.getLogger(__name__)


def transform_day(day):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute((SQL_DIR / "02_staging_view.sql").read_text(encoding="utf-8"))
                cur.execute((SQL_DIR / "03_daily_summary.sql").read_text(encoding="utf-8"))
                cur.execute(
                    (SQL_DIR / "04_refresh_summary.sql").read_text(encoding="utf-8"),
                    {"day": day},
                )
                log.info("%s: summary refreshed (%d city rows)", day, cur.rowcount)
    finally:
        conn.close()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Refresh the daily summary.")
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    transform_day(parser.parse_args().date)


if __name__ == "__main__":
    main()