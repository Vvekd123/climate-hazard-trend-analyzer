
from datetime import date, timedelta


def detect_heatwaves(observations, min_days=3):
    """
    Detect heatwaves using consecutive days above their
    corresponding temperature thresholds.

    Each observation must contain:
    - date: YYYY-MM-DD
    - temperature_max: maximum temperature in Celsius
    - threshold: temperature threshold in Celsius

    Missing temperatures or thresholds break a heatwave run.
    """

    if min_days < 1:
        raise ValueError("min_days must be at least 1")

    observations = sorted(
        observations,
        key=lambda item: date.fromisoformat(item["date"])
    )

    dates = [date.fromisoformat(item["date"]) for item in observations]

    if len(dates) != len(set(dates)):
        raise ValueError("Duplicate observation dates are not allowed")

    events = []
    current_run = []
    previous_date = None

    def save_event(run):
        if len(run) < min_days:
            return

        temperatures = [item["temperature_max"] for item in run]
        excesses = [
            item["temperature_max"] - item["threshold"]
            for item in run
        ]

        events.append({
            "start_date": run[0]["date"],
            "end_date": run[-1]["date"],
            "duration_days": len(run),
            "peak_temperature_c": max(temperatures),
            "mean_excess_c": round(
                sum(excesses) / len(excesses), 2
            ),
        })

    for item in observations:
        current_date = date.fromisoformat(item["date"])

        # A missing calendar day breaks consecutiveness.
        if (
            previous_date is not None
            and current_date != previous_date + timedelta(days=1)
        ):
            save_event(current_run)
            current_run = []

        temperature = item["temperature_max"]
        threshold = item["threshold"]

        # Missing measurements cannot be treated as hot days.
        if temperature is None or threshold is None:
            save_event(current_run)
            current_run = []
        elif temperature > threshold:
            current_run.append(item)
        else:
            save_event(current_run)
            current_run = []

        previous_date = current_date

    # Do not forget a heatwave that continues through the final date.
    save_event(current_run)

    return events
