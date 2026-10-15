from datetime import date, datetime, timedelta, timezone

import pytest

from src.checks import check_freshness, check_rejected_ratio, check_row_counts
from src.extract import CITIES

DAY = date(2026, 10, 14)
NOW = datetime(2026, 10, 15, 6, 0, tzinfo=timezone.utc)


def full_counts():
    return {city: 24 for city in CITIES}


def test_all_cities_with_24_rows_pass():
    assert check_row_counts(full_counts()) == []


def test_short_city_fails():
    counts = full_counts()
    counts["Delhi"] = 23
    problems = check_row_counts(counts)
    assert len(problems) == 1 and "Delhi" in problems[0]


def test_missing_city_fails():
    counts = full_counts()
    del counts["Kochi"]
    assert "Kochi" in check_row_counts(counts)[0]


def test_fresh_complete_day_passes():
    problems = check_freshness(DAY, datetime(2026, 10, 14, 23, 0), NOW - timedelta(hours=1), NOW)
    assert problems == []


def test_incomplete_day_fails():
    problems = check_freshness(DAY, datetime(2026, 10, 14, 17, 0), NOW - timedelta(hours=1), NOW)
    assert any("latest hour" in p for p in problems)


def test_stale_load_fails():
    problems = check_freshness(DAY, datetime(2026, 10, 14, 23, 0), NOW - timedelta(hours=30), NOW)
    assert any("last load" in p for p in problems)


def test_no_data_fails():
    assert check_freshness(DAY, None, None, NOW) != []


@pytest.mark.parametrize("valid, rejected", [(100, 0), (96, 4), (99, 1)])
def test_low_rejection_passes(valid, rejected):
    assert check_rejected_ratio(valid, rejected) == []


@pytest.mark.parametrize("valid, rejected", [(95, 5), (90, 10)])
def test_five_percent_or_more_fails(valid, rejected):
    assert check_rejected_ratio(valid, rejected) != []


def test_empty_day_fails():
    assert check_rejected_ratio(0, 0) != []