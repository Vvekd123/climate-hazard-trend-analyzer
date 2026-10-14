
from datetime import date

from fastapi import FastAPI, HTTPException, Query

from app.services.analysis import analyze_heatwaves
from app.services.weather import fetch_daily_max_temperatures

app = FastAPI(
    title="Climate Hazard Trend Analyzer",
    description="Analyze historical climate hazards.",
    version="1.0.0",
)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Climate Hazard Trend Analyzer",
    }


@app.get("/api/weather-preview")
def weather_preview(
    latitude: float = Query(12.9716, ge=-90, le=90),
    longitude: float = Query(77.5946, ge=-180, le=180),
    start_date: date = date(2020, 5, 1),
    end_date: date = date(2020, 5, 7),
):
    try:
        observations = fetch_daily_max_temperatures(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "region": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "records_count": len(observations),
        "observations": observations,
    }


@app.get("/api/analyze")
def analyze_heatwave_endpoint(
    latitude: float = Query(12.9716, ge=-90, le=90),
    longitude: float = Query(77.5946, ge=-180, le=180),
    start_date: date = date(2020, 5, 1),
    end_date: date = date(2020, 5, 7),
    baseline_start: date = date(1991, 1, 1),
    baseline_end: date = date(2020, 12, 31),
    percentile: float = Query(95, gt=0, le=100),
    min_days: int = Query(3, ge=1),
    window_days: int = Query(2, ge=0),
    min_samples: int = Query(30, ge=1),
):
    try:
        return analyze_heatwaves(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            percentile=percentile,
            min_days=min_days,
            window_days=window_days,
            min_samples=min_samples,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
