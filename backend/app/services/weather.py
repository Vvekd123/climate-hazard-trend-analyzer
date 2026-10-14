
from datetime import date

import httpx
from app.services.weather_cache import (
    get_cached_observations,
    save_observations,
)

OPEN_METEO_ARCHIVE_URL = (
    "https://archive-api.open-meteo.com/v1/archive"
)


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
    """Return cached observations or fetch and cache them."""
    # Preserve the existing input validation before checking the cache.
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

    if cached is not None:
        return cached

    observations = _fetch_from_open_meteo(
        latitude, longitude, start_date, end_date
    )

    save_observations(latitude, longitude, observations)
    return observations
