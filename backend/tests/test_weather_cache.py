import json
from datetime import date

import httpx
import pytest

from app.services import weather
from app.services.weather import WeatherRateLimitError


def setup_fake_cache(monkeypatch, initial_records=None):
    """Simulate MongoDB reads and writes using an in-memory list."""
    records = list(initial_records or [])

    def fake_get(latitude, longitude, start_date, end_date):
        return [
            item.copy()
            for item in records
            if start_date.isoformat() <= item["date"] <= end_date.isoformat()
        ]

    def fake_save(latitude, longitude, observations):
        for item in observations:
            existing = next(
                (
                    record for record in records
                    if record["date"] == item["date"]
                ),
                None,
            )

            if existing:
                existing.update(item)
            else:
                records.append(item.copy())

        return True

    monkeypatch.setattr(
        weather, "get_cached_observations", fake_get
    )
    monkeypatch.setattr(
        weather, "save_observations", fake_save
    )

    return records


def setup_cache_readback(monkeypatch, fetched, readback):
    read_count = 0

    def fake_get(latitude, longitude, start_date, end_date):
        nonlocal read_count
        read_count += 1
        if read_count == 1:
            return []
        if readback is None:
            return None
        return [item.copy() for item in readback]

    monkeypatch.setattr(weather, "get_cached_observations", fake_get)
    monkeypatch.setattr(weather, "save_observations", lambda *args: True)
    monkeypatch.setattr(
        weather,
        "_fetch_from_nasa_power",
        lambda *args: [item.copy() for item in fetched],
    )


def test_cache_hit_skips_nasa_power(monkeypatch):
    cached = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]

    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: cached
    )

    def unexpected_fetch(*args):
        raise AssertionError("NASA POWER should not be called on a cache hit")

    monkeypatch.setattr(weather, "_fetch_from_nasa_power", unexpected_fetch)

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 2)
    )

    assert result == cached


def test_cache_miss_fetches_saves_and_verifies_readback(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]
    saved = setup_fake_cache(monkeypatch)
    monkeypatch.setattr(
        weather, "_fetch_from_nasa_power", lambda *args: fetched
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 2)
    )

    assert result == fetched
    assert len(saved) == 2
    assert saved == fetched


def test_empty_cache_result_triggers_fetch(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
    ]
    saved = setup_fake_cache(monkeypatch)

    monkeypatch.setattr(
        weather, "_fetch_from_nasa_power", lambda *args: fetched
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 1)
    )

    assert result == fetched
    assert saved == fetched


def test_partial_cache_fetches_only_missing_dates(monkeypatch):
    from datetime import timedelta

    cached = [
        {"date": "2020-05-01", "temperature_max": 32.8},
        {"date": "2020-05-02", "temperature_max": 33.1},
        {"date": "2020-05-03", "temperature_max": 33.4},
    ]

    fetched_ranges = []
    saved = setup_fake_cache(monkeypatch, cached)

    def fake_fetch(latitude, longitude, start_date, end_date):
        fetched_ranges.append((start_date, end_date))
        records = []
        current = start_date

        while current <= end_date:
            records.append({
                "date": current.isoformat(),
                "temperature_max": 34.0,
            })
            current += timedelta(days=1)

        return records

    monkeypatch.setattr(
        weather, "_fetch_from_nasa_power", fake_fetch
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 7)
    )

    assert len(result) == 7
    assert [item["date"] for item in result] == [
        f"2020-05-{day:02d}" for day in range(1, 8)
    ]
    assert result[:3] == cached
    assert fetched_ranges == [(date(2020, 5, 4), date(2020, 5, 7))]
    assert len(saved) == 7
    assert len([item for item in saved if item["date"] >= "2020-05-04"]) == 4


def test_nasa_power_429_raises_rate_limit_error(monkeypatch):
    response = httpx.Response(
        429,
        request=httpx.Request(
            "GET", weather.NASA_POWER_DAILY_URL
        ),
    )

    monkeypatch.setattr(
        weather.httpx, "get", lambda *args, **kwargs: response
    )

    with pytest.raises(
        WeatherRateLimitError,
        match="rate limit reached",
    ):
        weather._fetch_from_nasa_power(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 3),
        )


@pytest.mark.parametrize(
    "raw_value",
    [float("nan"), float("inf"), float("-inf"), -999],
)
def test_invalid_and_fill_temperatures_are_cached_as_missing(
    monkeypatch,
    raw_value,
):
    saved = setup_fake_cache(monkeypatch)
    response = httpx.Response(
        200,
        content=json.dumps(
            {
                "properties": {
                    "parameter": {
                        "T2M_MAX": {"20200501": raw_value},
                    }
                }
            },
            allow_nan=True,
        ).encode(),
        headers={"content-type": "application/json"},
        request=httpx.Request("GET", weather.NASA_POWER_DAILY_URL),
    )
    monkeypatch.setattr(
        weather.httpx,
        "get",
        lambda *args, **kwargs: response,
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716,
        77.5946,
        date(2020, 5, 1),
        date(2020, 5, 1),
    )

    expected = [{"date": "2020-05-01", "temperature_max": None}]
    assert result == expected
    assert saved == expected
    json.dumps(result, allow_nan=False)


def test_non_numeric_nasa_temperature_keeps_runtime_error(monkeypatch):
    saved = setup_fake_cache(monkeypatch)
    response = httpx.Response(
        200,
        json={
            "properties": {
                "parameter": {
                    "T2M_MAX": {"20200501": "not-a-temperature"},
                }
            }
        },
        request=httpx.Request("GET", weather.NASA_POWER_DAILY_URL),
    )
    monkeypatch.setattr(
        weather.httpx,
        "get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(RuntimeError, match="Invalid temperature value"):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 1),
        )

    assert saved == []


def test_missing_nasa_value_is_returned_and_cached_as_none(monkeypatch):
    saved = setup_fake_cache(monkeypatch)
    response = httpx.Response(
        200,
        json={"properties": {"parameter": {"T2M_MAX": {}}}},
        request=httpx.Request("GET", weather.NASA_POWER_DAILY_URL),
    )
    monkeypatch.setattr(
        weather.httpx,
        "get",
        lambda *args, **kwargs: response,
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716,
        77.5946,
        date(2020, 5, 1),
        date(2020, 5, 1),
    )

    assert result[0]["temperature_max"] is None
    assert saved[0]["temperature_max"] is None


def test_cache_readback_accepts_matching_none_temperature(monkeypatch):
    fetched = [{"date": "2020-05-01", "temperature_max": None}]
    setup_cache_readback(monkeypatch, fetched, fetched)

    result = weather.fetch_daily_max_temperatures(
        12.9716,
        77.5946,
        date(2020, 5, 1),
        date(2020, 5, 1),
    )

    assert result == fetched


@pytest.mark.parametrize(
    "saved_temperature",
    [float("nan"), float("inf"), float("-inf"), -999],
)
def test_cache_readback_normalizes_missing_temperature_values(
    monkeypatch,
    saved_temperature,
):
    fetched = [{"date": "2020-05-01", "temperature_max": None}]
    readback = [{"date": "2020-05-01", "temperature_max": saved_temperature}]
    setup_cache_readback(monkeypatch, fetched, readback)

    result = weather.fetch_daily_max_temperatures(
        12.9716,
        77.5946,
        date(2020, 5, 1),
        date(2020, 5, 1),
    )

    assert result == fetched


def test_cache_readback_rejects_missing_and_unexpected_dates(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]
    readback = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-03", "temperature_max": 36.0},
    ]
    setup_cache_readback(monkeypatch, fetched, readback)

    with pytest.raises(
        RuntimeError,
        match="Could not verify the weather cache write",
    ):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 2),
        )


def test_cache_readback_rejects_duplicate_dates(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]
    readback = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-01", "temperature_max": 36.0},
    ]
    setup_cache_readback(monkeypatch, fetched, readback)

    with pytest.raises(
        RuntimeError,
        match="Could not verify the weather cache write",
    ):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 2),
        )


def test_cache_readback_rejects_temperature_mismatch(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]
    readback = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 99.0},
    ]
    setup_cache_readback(monkeypatch, fetched, readback)

    with pytest.raises(
        RuntimeError,
        match="Could not verify the weather cache write",
    ):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 2),
        )


def test_failed_cache_write_preserves_existing_error(monkeypatch):
    fetched = [{"date": "2020-05-01", "temperature_max": 35.0}]
    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: []
    )
    monkeypatch.setattr(weather, "save_observations", lambda *args: False)
    monkeypatch.setattr(
        weather,
        "_fetch_from_nasa_power",
        lambda *args: fetched,
    )

    with pytest.raises(
        RuntimeError,
        match="Could not save weather data to MongoDB",
    ):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 1),
        )


def test_cache_readback_failure_preserves_existing_error(monkeypatch):
    fetched = [{"date": "2020-05-01", "temperature_max": 35.0}]
    setup_cache_readback(monkeypatch, fetched, None)

    with pytest.raises(
        RuntimeError,
        match="Could not verify the weather cache write",
    ):
        weather.fetch_daily_max_temperatures(
            12.9716,
            77.5946,
            date(2020, 5, 1),
            date(2020, 5, 1),
        )


@pytest.mark.parametrize(
    "cached_value",
    [float("nan"), float("inf"), float("-inf"), -999],
)
def test_invalid_cached_temperatures_are_returned_as_none(
    monkeypatch,
    cached_value,
):
    cached = [{"date": "2020-05-01", "temperature_max": cached_value}]
    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: cached
    )

    def unexpected_fetch(*args):
        raise AssertionError("A cache hit should not fetch NASA POWER")

    monkeypatch.setattr(weather, "_fetch_from_nasa_power", unexpected_fetch)

    result = weather.fetch_daily_max_temperatures(
        12.9716,
        77.5946,
        date(2020, 5, 1),
        date(2020, 5, 1),
    )

    assert result[0]["temperature_max"] is None


def test_large_missing_range_is_fetched_in_chunks(monkeypatch):
    from datetime import timedelta

    start = date(2020, 1, 1)
    end = start + timedelta(days=365)

    fetched_ranges = []
    saved = setup_fake_cache(monkeypatch)
    def fake_fetch(latitude, longitude, chunk_start, chunk_end):
        fetched_ranges.append((chunk_start, chunk_end))
        records = []
        current = chunk_start

        while current <= chunk_end:
            records.append({
                "date": current.isoformat(),
                "temperature_max": 30.0,
            })
            current += timedelta(days=1)

        return records

    
    monkeypatch.setattr(
        weather, "_fetch_from_nasa_power", fake_fetch
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, start, end
    )

    assert len(result) == 366
    assert fetched_ranges == [
        (start, start + timedelta(days=364)),
        (start + timedelta(days=365), end),
    ]
