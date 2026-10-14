from datetime import date
import httpx
import pytest
from app.services import weather
from app.services.weather import WeatherRateLimitError
from app.services import weather


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


def test_cache_miss_fetches_and_saves(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]
    saved = []

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
    saved = []
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
    from datetime import date, timedelta

    cached = [
        {"date": "2020-05-01", "temperature_max": 32.8},
        {"date": "2020-05-02", "temperature_max": 33.1},
        {"date": "2020-05-03", "temperature_max": 33.4},
    ]

    fetched_ranges = []
    saved = []
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
