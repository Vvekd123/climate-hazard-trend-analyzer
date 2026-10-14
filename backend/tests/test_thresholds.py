
import pytest

from app.services.thresholds import (
    calculate_calendar_day_thresholds,
    calculate_percentile,
)


def test_calculates_95th_percentile():
    assert calculate_percentile([10, 20, 30, 40, 50], 95) == 48.0


def test_calculates_percentile_for_single_value():
    assert calculate_percentile([25], 95) == 25.0


def test_rejects_empty_values():
    with pytest.raises(ValueError, match="At least one"):
        calculate_percentile([], 95)


def test_rejects_invalid_percentile():
    with pytest.raises(ValueError, match="Percentile"):
        calculate_percentile([10, 20, 30], 101)


def test_rejects_non_finite_temperatures():
    with pytest.raises(ValueError, match="finite"):
        calculate_percentile([10, float("inf")], 95)


def test_calculates_calendar_day_threshold():
    baseline = [
        {
            "date": f"{year}-05-03",
            "temperature_max": float(year - 1990),
        }
        for year in range(1991, 2021)
    ]

    result = calculate_calendar_day_thresholds(
        baseline,
        ["2020-05-03"],
        window_days=0,
    )

    assert result["2020-05-03"] == 28.55


def test_ignores_missing_baseline_temperatures():
    baseline = [
        {"date": "2020-05-03", "temperature_max": 20.0},
        {"date": "2021-05-03", "temperature_max": None},
        {"date": "2022-05-03", "temperature_max": 30.0},
    ]

    result = calculate_calendar_day_thresholds(
        baseline,
        ["2020-05-03"],
        window_days=0,
        min_samples=2,
    )

    assert result["2020-05-03"] == 29.5


def test_rejects_insufficient_baseline_samples():
    baseline = [
        {"date": "2020-05-03", "temperature_max": 30.0},
    ]

    with pytest.raises(ValueError, match="Insufficient baseline"):
        calculate_calendar_day_thresholds(
            baseline,
            ["2020-05-03"],
        )


def test_calendar_window_wraps_across_year_boundary():
    baseline = []

    for year in range(1991, 2021):
        baseline.extend([
            {"date": f"{year}-12-31", "temperature_max": 20.0},
            {"date": f"{year}-01-01", "temperature_max": 30.0},
        ])

    result = calculate_calendar_day_thresholds(
        baseline,
        ["2020-01-01"],
        window_days=1,
    )

    assert result["2020-01-01"] == 30.0


def test_february_29_is_supported():
    baseline = [
        {"date": f"{year}-02-29", "temperature_max": float(year - 1990)}
        for year in range(1992, 2020, 4)
    ]

    result = calculate_calendar_day_thresholds(
        baseline,
        ["2020-02-29"],
        window_days=0,
        min_samples=1,
    )

    assert result["2020-02-29"] == 24.8
