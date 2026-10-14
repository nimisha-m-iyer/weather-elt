import pytest

from src.validate import rows_from_raw, validate_row, validate_rows


def make_row(**overrides):
    """A good row, with any fields we want to break."""
    row = {
        "city": "Kochi",
        "hour": "2026-10-13T10:00",
        "temperature_2m": 30.0,
        "relative_humidity_2m": 70,
        "precipitation": 0.0,
        "wind_speed_10m": 8.5,
    }
    row.update(overrides)
    return row


def test_good_row_passes():
    assert validate_row(make_row()) is None


@pytest.mark.parametrize("field", [
    "temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m",
])
def test_null_value_is_rejected(field):
    reason = validate_row(make_row(**{field: None}))
    assert reason == f"missing value: {field}"


def test_missing_hour_is_rejected():
    assert validate_row(make_row(hour=None)) == "missing hour"


def test_invalid_hour_is_rejected():
    assert "invalid hour" in validate_row(make_row(hour="not-a-time"))


@pytest.mark.parametrize("temp", [-10.1, -50, 55.1, 400])
def test_impossible_temperature_is_rejected(temp):
    assert "temperature out of range" in validate_row(make_row(temperature_2m=temp))


@pytest.mark.parametrize("temp", [-10, 55, 0, 30.5])
def test_boundary_temperatures_are_accepted(temp):
    assert validate_row(make_row(temperature_2m=temp)) is None


@pytest.mark.parametrize("humidity", [-1, 100.1, 150])
def test_humidity_out_of_range_is_rejected(humidity):
    assert "humidity out of range" in validate_row(make_row(relative_humidity_2m=humidity))


@pytest.mark.parametrize("humidity", [0, 100])
def test_boundary_humidity_is_accepted(humidity):
    assert validate_row(make_row(relative_humidity_2m=humidity)) is None


def test_negative_rain_is_rejected():
    assert "negative precipitation" in validate_row(make_row(precipitation=-0.1))


def test_negative_wind_is_rejected():
    assert "negative wind speed" in validate_row(make_row(wind_speed_10m=-1))


def test_nan_is_rejected():
    assert "NaN" in validate_row(make_row(temperature_2m=float("nan")))


def test_text_value_is_rejected():
    assert "non-numeric" in validate_row(make_row(temperature_2m="hot"))


def test_validate_rows_splits_good_and_bad():
    rows = [make_row(), make_row(temperature_2m=999), make_row(wind_speed_10m=None)]
    valid, rejected = validate_rows(rows)
    assert len(valid) == 1
    assert len(rejected) == 2
    assert all("reason" in r for r in rejected)


def test_rows_from_raw_flips_columns_into_rows():
    data = {"hourly": {
        "time": ["2026-10-13T00:00", "2026-10-13T01:00"],
        "temperature_2m": [26.4, 26.1],
        "relative_humidity_2m": [88, 89],
        "precipitation": [0.0, 0.0],
        "wind_speed_10m": [6.1, 5.8],
    }}
    rows = rows_from_raw("Kochi", data)
    assert len(rows) == 2
    assert rows[0]["city"] == "Kochi"
    assert rows[1]["temperature_2m"] == 26.1


def test_short_column_becomes_missing_value():
    data = {"hourly": {
        "time": ["2026-10-13T00:00", "2026-10-13T01:00"],
        "temperature_2m": [26.4],          # one value short
        "relative_humidity_2m": [88, 89],
        "precipitation": [0.0, 0.0],
        "wind_speed_10m": [6.1, 5.8],
    }}
    valid, rejected = validate_rows(rows_from_raw("Kochi", data))
    assert len(valid) == 1
    assert rejected[0]["reason"] == "missing value: temperature_2m"