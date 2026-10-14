# Climate Hazard Trend Analyzer

A full-stack application for analyzing historical climate data, detecting heatwave events, and exploring temperature trends.

## Project Status

**In development.**

### Implemented
- FastAPI backend setup.
- Health-check endpoint.
- Historical daily maximum-temperature retrieval using the Open-Meteo Archive API.
- Heatwave detection based on consecutive days exceeding supplied temperature thresholds.
- Calendar-day-specific percentile threshold calculation.
- Unit tests for heatwave detection and threshold calculations.

### Planned
- End-to-end climate analysis API.
- Annual heatwave frequency and duration summaries.
- Persistent storage and caching using a NoSQL database.
- React and TypeScript frontend with interactive charts.
- Deployment and downloadable analysis reports.

## Technology Stack

### Backend
- Python
- FastAPI
- HTTPX
- Pytest

### Frontend
- React
- TypeScript
- To be implemented

### Data Source
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)

### Planned Database
- MongoDB

## Current API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/weather-preview` | Retrieve historical daily maximum temperatures for a selected coordinate and date range |

Interactive API documentation is available at `/docs` while the backend is running locally.

## Heatwave Detection Approach

The current detector identifies a heatwave when daily maximum temperatures exceed their corresponding thresholds for at least three consecutive calendar days.

The detector:
- Requires each observation to have a date, maximum temperature, and threshold.
- Ends a qualifying run when a temperature or threshold is missing.
- Ends a run when a calendar day is missing.
- Returns event start date, end date, duration, peak temperature, and mean temperature excess.

## Temperature Threshold Method

The current threshold service calculates calendar-day-specific percentile thresholds.

The initial methodology uses:
- A planned historical baseline of 1991–2020.
- The 95th percentile.
- A five-calendar-day window: the target day and two days on either side.
- Linear interpolation to calculate percentiles.
- Missing-temperature exclusion and a minimum valid sample requirement.

The analysis service still needs to connect the historical baseline retrieval to this calculation and verify data coverage. The baseline period and percentile method will be documented and validated as part of the completed analysis workflow.

## Local Development

### Prerequisites
- Python 3.10 or later
- Git

### Setup the backend

From the repository root, open PowerShell and run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Start the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open the following URLs in your browser:

- Health check: `http://127.0.0.1:8000/api/health`
- Weather preview: `http://127.0.0.1:8000/api/weather-preview`
- API documentation: `http://127.0.0.1:8000/docs`

### Run tests

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

## Project Structure

```text
climate-hazard-trend-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── weather.py
│   │       ├── heatwave.py
│   │       └── thresholds.py
│   ├── tests/
│   │   ├── test_heatwave.py
│   │   ├── test_thresholds.py
│   │   └── test_health.py
│   └── requirements.txt
├── frontend/
├── .gitignore
└── README.md
```

## Current Testing Status

The backend currently has 15 passing unit tests covering heatwave detection and percentile threshold calculations.

## License

To be determined.