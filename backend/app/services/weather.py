
from datetime import date, timedelta

import httpx

from app.services.weather_cache import (
    get_cached_observations,
    save_observations,
)

NASA_POWER_DAILY_URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point"
)


class WeatherRateLimitError(RuntimeError):
    """Raised when the weather provider rate-limits a request."""


def _fetch_from_nasa_power(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch daily maximum temperatures from NASA POWER in Celsius."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if start_date > end_date:
        raise ValueError("Start date must not be after end date")

    if (end_date - start_date).days > 40 * 366:
        raise ValueError("Date range cannot exceed 40 years")

    params = {
        "parameters": "T2M_MAX",
        "community": "RE",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }

    try:
        response = httpx.get(
            NASA_POWER_DAILY_URL,
            params=params,
            timeout=90.0,
        )

        if response.status_code == 429:
            raise WeatherRateLimitError(
                "NASA POWER rate limit reached. "
                "Saved cache data is preserved; retry later."
            )

        response.raise_for_status()
        payload = response.json()

    except WeatherRateLimitError:
        raise
    except httpx.TimeoutException as exc:
        raise RuntimeError("Weather API request timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Weather API returned HTTP {exc.response.status_code}"
        ) from exc
    except httpx.RequestError as exc:
        raise RuntimeError("Could not connect to weather API") from exc
    except ValueError as exc:
        raise RuntimeError("Weather API returned invalid JSON") from exc

    try:
        values = payload["properties"]["parameter"]["T2M_MAX"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(
            "NASA POWER response is missing T2M_MAX data"
        ) from exc

    if not isinstance(values, dict):
        raise RuntimeError("NASA POWER returned invalid daily data")

    observations = []
    current = start_date

    while current <= end_date:
        day = current.isoformat()
        raw_value = values.get(current.strftime("%Y%m%d"))

        # NASA POWER uses -999 for unavailable parameter values.
        temperature = None

        if raw_value is not None:
            try:
                numeric_value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    f"Invalid temperature value for {day}"
                ) from exc

            if numeric_value != -999:
                temperature = numeric_value

        observations.append({
            "date": day,
            "temperature_max": temperature,
        })

        current += timedelta(days=1)

    return observations


def fetch_daily_max_temperatures(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Return cached observations and fetch missing dates from NASA POWER."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if start_date > end_date:
        raise ValueError("Start date must not be after end date")

    if (end_date - start_date).days > 40 * 366:
        raise ValueError("Date range cannot exceed 40 years")

    cached = get_cached_observations(
        latitude, longitude, start_date, end_date
    )

    if cached is None:
        raise RuntimeError(
            "MongoDB cache is unavailable. "
            "Restore the database connection before fetching data."
        )

    observations_by_date = {
        item["date"]: item for item in cached
    }

    missing_dates = []
    current = start_date

    while current <= end_date:
        if current.isoformat() not in observations_by_date:
            missing_dates.append(current)
        current += timedelta(days=1)

    index = 0
    max_chunk_days = 365

    while index < len(missing_dates):
        missing_start = missing_dates[index]
        run_end = missing_start
        index += 1

        while (
            index < len(missing_dates)
            and missing_dates[index] == run_end + timedelta(days=1)
        ):
            run_end = missing_dates[index]
            index += 1

        chunk_start = missing_start

        while chunk_start <= run_end:
            chunk_end = min(
                chunk_start + timedelta(days=max_chunk_days - 1),
                run_end,
            )

            fetched = _fetch_from_nasa_power(
                latitude, longitude, chunk_start, chunk_end
            )

            # Verify the MongoDB write before marking the batch complete.
            saved_successfully = save_observations(
                latitude, longitude, fetched
            )

            if not saved_successfully:
                raise RuntimeError(
                    "Could not save weather data to MongoDB. "
                    "Check database connectivity and logs."
                )

            saved = get_cached_observations(
                latitude, longitude, chunk_start, chunk_end
            )

            if saved is None or len(saved) != len(fetched):
                raise RuntimeError(
                    "Could not verify the weather cache write. "
                    "Check MongoDB connectivity and logs."
                )

            for item in saved:
                observations_by_date[item["date"]] = item

            chunk_start = chunk_end + timedelta(days=1)

    return [
        observations_by_date[
            (start_date + timedelta(days=offset)).isoformat()
        ]
        for offset in range((end_date - start_date).days + 1)
        if (
            start_date + timedelta(days=offset)
        ).isoformat() in observations_by_date
    ]
