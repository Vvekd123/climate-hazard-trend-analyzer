
from datetime import date
from math import isfinite


def calculate_percentile(
    values: list[float],
    percentile: float,
) -> float:
    """Calculate a percentile using linear interpolation."""
    if not values:
        raise ValueError("At least one temperature is required")

    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")

    if any(not isfinite(value) for value in values):
        raise ValueError("Temperatures must be finite numbers")

    sorted_values = sorted(values)
    position = (len(sorted_values) - 1) * percentile / 100

    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index

    result = (
        sorted_values[lower_index] * (1 - fraction)
        + sorted_values[upper_index] * fraction
    )

    return round(result, 2)


def _calendar_day_index(day: date) -> int:
    """Map a date to a leap-year calendar so Feb 29 is supported."""
    reference_date = date(2000, day.month, day.day)
    return (reference_date - date(2000, 1, 1)).days


def calculate_calendar_day_thresholds(
    baseline_observations: list[dict],
    target_dates: list[str],
    percentile: float = 95,
    window_days: int = 2,
    min_samples: int = 30,
) -> dict[str, float]:
    """
    Calculate calendar-day-specific temperature thresholds.

    Each observation contains:
        date: YYYY-MM-DD
        temperature_max: temperature in Celsius, or None

    For each target date, use valid baseline temperatures within
    +/- window_days of its calendar day, across all baseline years.
    """
    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")

    if window_days < 0:
        raise ValueError("window_days cannot be negative")

    if min_samples < 1:
        raise ValueError("min_samples must be at least 1")

    normalized_baseline = []

    for observation in baseline_observations:
        day = date.fromisoformat(observation["date"])
        temperature = observation["temperature_max"]

        if temperature is None:
            continue

        if isinstance(temperature, bool) or not isinstance(
            temperature, (int, float)
        ):
            raise ValueError("Temperatures must be numeric or None")

        temperature = float(temperature)

        if not isfinite(temperature):
            raise ValueError("Temperatures must be finite numbers")

        normalized_baseline.append(
            (_calendar_day_index(day), temperature)
        )

    if not normalized_baseline:
        raise ValueError("No valid baseline temperatures available")

    calendar_length = 366
    thresholds = {}

    for target_string in target_dates:
        target = date.fromisoformat(target_string)
        target_index = _calendar_day_index(target)
        temperatures = []

        for baseline_index, temperature in normalized_baseline:
            distance = abs(baseline_index - target_index)
            distance = min(distance, calendar_length - distance)

            if distance <= window_days:
                temperatures.append(temperature)

        if len(temperatures) < min_samples:
            raise ValueError(
                f"Insufficient baseline samples for {target_string}: "
                f"found {len(temperatures)}, need {min_samples}"
            )

        thresholds[target_string] = calculate_percentile(
            temperatures,
            percentile,
        )

    return thresholds
