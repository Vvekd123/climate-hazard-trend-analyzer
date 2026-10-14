
from datetime import date, timedelta

import pytest

from app.services import analysis


def make_baseline():
    """Generate 30 years of temperatures for a small calendar window."""
    records = []

    for year in range(1991, 2021):
        for day_number in range(1, 10):
            records.append({
                "date": f"{year}-05-{day_number:02d}",
                "temperature_max": float(20 + day_number % 5),
            })

    return records


def make_analysis_observations():
    temperatures = [35.0, 36.0, 35.0, 20.0, 20.0, 35.0, 36.0]
    start = date(2020, 5, 1)

    return [
        {
            "date": (start + timedelta(days=index)).isoformat(),
            "temperature_max": temperature,
        }
        for index, temperature in enumerate(temperatures)
    ]


def test_analyze_heatwaves_returns_events_and_summary(monkeypatch):
    baseline = make_baseline()
    observations = make_analysis_observations()
    fetch_calls = []

    def fake_fetch(
        latitude,
        longitude,
        start_date,
        end_date,
    ):
        fetch_calls.append((start_date, end_date))

        if start_date == date(1991, 1, 1):
            return baseline

        return observations

    monkeypatch.setattr(
        analysis,
        "fetch_daily_max_temperatures",
        fake_fetch,
    )

    result = analysis.analyze_heatwaves(
        latitude=12.9716,
        longitude=77.5946,
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 7),
    )

    assert len(fetch_calls) == 2
    assert result["summary"]["total_events"] == 1
    assert result["summary"]["annual_frequency"] == {"2020": 1}
    assert result["summary"]["average_duration_days"] == 3
    assert result["summary"]["longest_event_days"] == 3

    event = result["events"][0]
    assert event["start_date"] == "2020-05-01"
    assert event["end_date"] == "2020-05-03"
    assert event["duration_days"] == 3

    assert len(result["daily_observations"]) == 7
    assert all(
        "threshold" in item
        for item in result["daily_observations"]
    )


def test_rejects_invalid_analysis_date_range():
    with pytest.raises(ValueError, match="Analysis start date"):
        analysis.analyze_heatwaves(
            latitude=12.9716,
            longitude=77.5946,
            start_date=date(2020, 5, 7),
            end_date=date(2020, 5, 1),
        )


def test_rejects_invalid_baseline_date_range():
    with pytest.raises(ValueError, match="Baseline start date"):
        analysis.analyze_heatwaves(
            latitude=12.9716,
            longitude=77.5946,
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 7),
            baseline_start=date(2021, 1, 1),
            baseline_end=date(2020, 1, 1),
        )


def test_rejects_empty_analysis_data(monkeypatch):
    def fake_fetch(
        latitude,
        longitude,
        start_date,
        end_date,
    ):
        if start_date == date(1991, 1, 1):
            return make_baseline()
        return []

    monkeypatch.setattr(
        analysis,
        "fetch_daily_max_temperatures",
        fake_fetch,
    )

    with pytest.raises(ValueError, match="No observations"):
        analysis.analyze_heatwaves(
            latitude=12.9716,
            longitude=77.5946,
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 7),
        )

def test_reports_missing_analysis_dates(monkeypatch):
    baseline = make_baseline()

    # May 4 is absent from the analysis response.
    observations = make_analysis_observations()
    observations = [
        item for item in observations
        if item["date"] != "2020-05-04"
    ]

    def fake_fetch(latitude, longitude, start_date, end_date):
        if start_date == date(1991, 1, 1):
            return baseline
        return observations

    monkeypatch.setattr(
        analysis,
        "fetch_daily_max_temperatures",
        fake_fetch,
    )

    result = analysis.analyze_heatwaves(
        latitude=12.9716,
        longitude=77.5946,
        start_date=date(2020, 5, 1),
        end_date=date(2020, 5, 7),
    )

    assert result["data_quality"]["missing_analysis_dates"] == [
        "2020-05-04"
    ]
    assert result["data_quality"]["missing_analysis_date_count"] == 1


def test_rejects_invalid_latitude():
    with pytest.raises(ValueError, match="Latitude"):
        analysis.analyze_heatwaves(
            latitude=91,
            longitude=77.5946,
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 7),
        )


def test_rejects_negative_window_days():
    with pytest.raises(ValueError, match="window_days"):
        analysis.analyze_heatwaves(
            latitude=12.9716,
            longitude=77.5946,
            start_date=date(2020, 5, 1),
            end_date=date(2020, 5, 7),
            window_days=-1,
        )
