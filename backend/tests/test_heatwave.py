
from app.services.heatwave import detect_heatwaves


def make_observations(temperatures):
    return [
        {
            "date": f"2020-05-{day:02d}",
            "temperature_max": temperature,
            "threshold": 35.0,
        }
        for day, temperature in enumerate(temperatures, start=1)
    ]


def test_detects_three_consecutive_hot_days():
    observations = make_observations([36, 37, 38])

    events = detect_heatwaves(observations)

    assert len(events) == 1
    assert events[0]["duration_days"] == 3
    assert events[0]["peak_temperature_c"] == 38
    assert events[0]["mean_excess_c"] == 2.0


def test_ignores_two_consecutive_hot_days():
    observations = make_observations([36, 37, 34])

    assert detect_heatwaves(observations) == []


def test_detects_separate_heatwave_events():
    observations = make_observations([36, 36, 36, 34, 37, 37, 37])

    events = detect_heatwaves(observations)

    assert len(events) == 2
    assert events[0]["duration_days"] == 3
    assert events[1]["duration_days"] == 3


def test_missing_temperature_breaks_a_run():
    observations = make_observations([36, 36, None, 36, 36])

    assert detect_heatwaves(observations) == []


def test_missing_calendar_day_breaks_a_run():
    observations = [
        {"date": "2020-05-01", "temperature_max": 36, "threshold": 35},
        {"date": "2020-05-02", "temperature_max": 36, "threshold": 35},
        {"date": "2020-05-04", "temperature_max": 36, "threshold": 35},
        {"date": "2020-05-05", "temperature_max": 36, "threshold": 35},
    ]

    assert detect_heatwaves(observations) == []
