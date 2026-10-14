from datetime import date

from app.services import weather


def test_cache_hit_skips_open_meteo(monkeypatch):
    cached = [
        {"date": "2020-05-01", "temperature_max": 35.0},
        {"date": "2020-05-02", "temperature_max": 36.0},
    ]

    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: cached
    )

    def unexpected_fetch(*args):
        raise AssertionError("Open-Meteo should not be called on a cache hit")

    monkeypatch.setattr(weather, "_fetch_from_open_meteo", unexpected_fetch)

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

    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: None
    )
    monkeypatch.setattr(
        weather, "_fetch_from_open_meteo", lambda *args: fetched
    )
    monkeypatch.setattr(
        weather, "save_observations",
        lambda latitude, longitude, observations:
            saved.append((latitude, longitude, observations)),
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 2)
    )

    assert result == fetched
    assert len(saved) == 1
    assert saved[0][2] == fetched


def test_empty_cache_result_triggers_fetch(monkeypatch):
    fetched = [
        {"date": "2020-05-01", "temperature_max": 35.0},
    ]
    saved = []

    monkeypatch.setattr(
        weather, "get_cached_observations", lambda *args: None
    )
    monkeypatch.setattr(
        weather, "_fetch_from_open_meteo", lambda *args: fetched
    )
    monkeypatch.setattr(
        weather, "save_observations",
        lambda *args: saved.append(args),
    )

    result = weather.fetch_daily_max_temperatures(
        12.9716, 77.5946, date(2020, 5, 1), date(2020, 5, 1)
    )

    assert result == fetched
    assert len(saved) == 1
