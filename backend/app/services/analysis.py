
from collections import Counter
from datetime import date, timedelta

from app.services.heatwave import detect_heatwaves
from app.services.thresholds import calculate_calendar_day_thresholds
from app.services.weather import fetch_daily_max_temperatures


def _validate_observations(
    observations: list[dict],
    start_date: date,
    end_date: date,
    label: str,
) -> None:
    """Validate dates returned by the weather service."""
    seen_dates = set()

    for item in observations:
        try:
            observation_date = date.fromisoformat(item["date"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"{label} contains an invalid observation date"
            ) from exc

        if not start_date <= observation_date <= end_date:
            raise ValueError(
                f"{label} contains a date outside the requested range: "
                f"{observation_date.isoformat()}"
            )

        if observation_date in seen_dates:
            raise ValueError(
                f"{label} contains duplicate date: "
                f"{observation_date.isoformat()}"
            )

        seen_dates.add(observation_date)


def _find_missing_dates(
    observations: list[dict],
    start_date: date,
    end_date: date,
) -> list[str]:
    """Return calendar dates absent from the observations."""
    observed_dates = {
        date.fromisoformat(item["date"])
        for item in observations
    }

    missing_dates = []
    current_date = start_date

    while current_date <= end_date:
        if current_date not in observed_dates:
            missing_dates.append(current_date.isoformat())

        current_date += timedelta(days=1)

    return missing_dates


def calculate_annual_trend(
    annual_frequency: dict[str, int],
    start_date: date,
    end_date: date,
) -> dict:
    """
    Calculate a descriptive trend from complete calendar years only.

    The slope represents the change in heatwave events per year. It is
    descriptive and is not a statistical significance test.
    """
    years = sorted(int(year) for year in annual_frequency)
    complete_years = [
        year
        for year in years
        if (year > start_date.year or start_date == date(year, 1, 1))
        and (year < end_date.year or end_date == date(year, 12, 31))
    ]

    if len(complete_years) < 5:
        return {
            "method": "ordinary_least_squares",
            "available": False,
            "reason": "At least 5 complete calendar years are required.",
            "years_analyzed": len(complete_years),
            "slope_events_per_year": None,
            "slope_events_per_decade": None,
            "direction": "insufficient_data",
            "insight": (
                "Trend estimation requires at least 5 complete calendar "
                "years; partial endpoint years are excluded."
            ),
        }

    # Center the years to keep the calculation numerically stable.
    mean_year = sum(complete_years) / len(complete_years)
    frequencies = [
        annual_frequency[str(year)] for year in complete_years
    ]
    mean_frequency = sum(frequencies) / len(frequencies)

    numerator = sum(
        (year - mean_year) * (frequency - mean_frequency)
        for year, frequency in zip(complete_years, frequencies)
    )
    denominator = sum(
        (year - mean_year) ** 2 for year in complete_years
    )

    slope = numerator / denominator
    slope_per_decade = slope * 10

    if slope > 1e-9:
        direction = "increasing"
        insight = (
            f"Annual heatwave frequency shows a descriptive "
            f"increasing trend of approximately "
            f"{slope_per_decade:.2f} events per decade."
        )
    elif slope < -1e-9:
        direction = "decreasing"
        insight = (
            f"Annual heatwave frequency shows a descriptive "
            f"decreasing trend of approximately "
            f"{abs(slope_per_decade):.2f} events per decade."
        )
    else:
        direction = "stable"
        insight = (
            "Annual heatwave frequency shows approximately "
            "no linear trend over the selected period."
        )

    return {
        "method": "ordinary_least_squares",
        "available": True,
        "years_analyzed": len(complete_years),
        "start_year": complete_years[0],
        "end_year": complete_years[-1],
        "slope_events_per_year": round(slope, 4),
        "slope_events_per_decade": round(slope_per_decade, 2),
        "direction": direction,
        "insight": insight,
    }



def analyze_heatwaves(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    baseline_start: date = date(1991, 1, 1),
    baseline_end: date = date(2020, 12, 31),
    percentile: float = 95,
    min_days: int = 3,
    window_days: int = 2,
    min_samples: int = 30,
) -> dict:
    """Analyze heatwave events for a region and date range."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if start_date > end_date:
        raise ValueError("Analysis start date must not be after end date")

    if baseline_start > baseline_end:
        raise ValueError(
            "Baseline start date must not be after baseline end date"
        )

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")

    if min_days < 1:
        raise ValueError("min_days must be at least 1")

    if window_days < 0:
        raise ValueError("window_days cannot be negative")

    if min_samples < 1:
        raise ValueError("min_samples must be at least 1")

    baseline_observations = fetch_daily_max_temperatures(
        latitude=latitude,
        longitude=longitude,
        start_date=baseline_start,
        end_date=baseline_end,
    )

    observations = fetch_daily_max_temperatures(
        latitude=latitude,
        longitude=longitude,
        start_date=start_date,
        end_date=end_date,
    )

    if not baseline_observations:
        raise ValueError("No observations available for the baseline period")

    if not observations:
        raise ValueError("No observations available for the analysis period")

    _validate_observations(
        baseline_observations,
        baseline_start,
        baseline_end,
        "Baseline data",
    )
    _validate_observations(
        observations,
        start_date,
        end_date,
        "Analysis data",
    )

    missing_dates = _find_missing_dates(
        observations,
        start_date,
        end_date,
    )

    target_dates = [item["date"] for item in observations]

    thresholds = calculate_calendar_day_thresholds(
        baseline_observations=baseline_observations,
        target_dates=target_dates,
        percentile=percentile,
        window_days=window_days,
        min_samples=min_samples,
    )

    enriched_observations = [
        {
            **item,
            "threshold": thresholds[item["date"]],
        }
        for item in observations
    ]

    events = detect_heatwaves(
        enriched_observations,
        min_days=min_days,
    )

    events_per_year = Counter(
        date.fromisoformat(event["start_date"]).year
        for event in events
    )

    annual_frequency = {
        str(year): events_per_year.get(year, 0)
        for year in range(start_date.year, end_date.year + 1)
    }
    trend = calculate_annual_trend(
        annual_frequency,
        start_date=start_date,
        end_date=end_date,
    )

    durations = [event["duration_days"] for event in events]

    return {
        "region": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "analysis_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "baseline_period": {
            "start_date": baseline_start.isoformat(),
            "end_date": baseline_end.isoformat(),
        },
        "methodology": {
            "percentile": percentile,
            "window_days": window_days,
            "minimum_consecutive_days": min_days,
        },
        "data_quality": {
            "analysis_records_received": len(observations),
            "missing_analysis_dates": missing_dates,
            "missing_analysis_date_count": len(missing_dates),
            "missing_temperature_dates": [
                item["date"]
                for item in observations
                if item["temperature_max"] is None
            ],
            "missing_temperature_date_count": sum(
                item["temperature_max"] is None
                for item in observations
            ),
        },
        "summary": {
            "total_events": len(events),
            "annual_frequency": annual_frequency,
            "trend": trend,
            "average_duration_days": (
                round(sum(durations) / len(durations), 2)
                if durations else 0
            ),
            "longest_event_days": max(durations) if durations else 0,
        },
        "events": events,
        "daily_observations": enriched_observations,
    }
