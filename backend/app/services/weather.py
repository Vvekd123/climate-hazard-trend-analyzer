from datetime import date, timedelta
import httpx
from app.services.weather_cache import (
    get_cached_observations,
    save_observations,
)

OPEN_METEO_ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


class WeatherRateLimitError(RuntimeError):
    """Raised when Open-Meteo temporarily rate-limits a request."""


def _fetch_from_open_meteo(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch daily maximum temperatures from Open-Meteo."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180")

    if start_date > end_date:
        raise ValueError("Start date must not be after end date")

    if (end_date - start_date).days > 40 * 366:
        raise ValueError("Date range cannot exceed 40 years")

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_max",
        "timezone": "UTC",
    }

    try:
        response = httpx.get(
            OPEN_METEO_ARCHIVE_URL,
            params=params,
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()

    except httpx.TimeoutException as exc:
        raise RuntimeError("Weather API request timed out") from exc

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 429:
            raise WeatherRateLimitError(
                "Weather provider rate limit reached. "
                "Cached data has been preserved; please try again later."
            ) from exc

        raise RuntimeError(
            f"Weather API returned HTTP {exc.response.status_code}"
        ) from exc

    except httpx.RequestError as exc:
        raise RuntimeError("Could not connect to weather API") from exc

    daily = payload.get("daily")

    if not isinstance(daily, dict):
        raise RuntimeError("Weather API returned an invalid response")

    dates = daily.get("time")
    temperatures = daily.get("temperature_2m_max")

    if (
        not isinstance(dates, list)
        or not isinstance(temperatures, list)
        or len(dates) != len(temperatures)
    ):
        raise RuntimeError("Weather API returned incomplete daily data")

    observations = []

    for day, temperature in zip(dates, temperatures):
        # Validate dates and preserve missing temperatures as None.
        date.fromisoformat(day)

        if temperature is not None and not isinstance(
            temperature, (int, float)
        ):
            raise RuntimeError("Invalid temperature value received")

        observations.append({
            "date": day,
            "temperature_max": (
                float(temperature)
                if temperature is not None
                else None
            ),
        })

    return observations


def fetch_daily_max_temperatures(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Return cached observations and fetch only missing dates."""
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

    # MongoDB unavailable: preserve the existing direct-fetch fallback.
    if cached is None:
        observations = _fetch_from_open_meteo(
            latitude, longitude, start_date, end_date
        )
        save_observations(latitude, longitude, observations)
        return observations

    # Index cached records by date for efficient lookup.
    observations_by_date = {
        item["date"]: item for item in cached
    }

    missing_dates = []
    current_date = start_date

    while current_date <= end_date:
        if current_date.isoformat() not in observations_by_date:
            missing_dates.append(current_date)
        current_date += timedelta(days=1)


    # Fetch each consecutive run of missing dates in chunks of at
    # most one year. Save every successful chunk immediately.
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

            fetched = _fetch_from_open_meteo(
                latitude, longitude, chunk_start, chunk_end
            )

            save_observations(latitude, longitude, fetched)

            for item in fetched:
                observations_by_date[item["date"]] = item

            chunk_start = chunk_end + timedelta(days=1)


    return [
        observations_by_date[day.isoformat()]
        for day in (
            start_date + timedelta(days=offset)
            for offset in range((end_date - start_date).days + 1)
        )
        if day.isoformat() in observations_by_date
    ]
