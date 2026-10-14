# Climate Hazard Trend Analyzer

A full-stack application for analyzing historical climate data, detecting heatwave events, and exploring temperature trends.

## Project Status

**In development.** The FastAPI backend and React/TypeScript dashboard are implemented. The backend test suite currently contains 22 passing tests. Deployment and additional analysis features remain in progress.

### Implemented

**Backend**
- FastAPI endpoints for health checks, weather previews, and heatwave analysis.
- Historical daily maximum-temperature retrieval using the Open-Meteo Archive API.
- Calendar-day-specific 95th-percentile threshold calculation using a configurable moving window.
- Heatwave detection based on consecutive days exceeding their thresholds.
- Annual event-frequency and event-duration summaries.
- Missing-data reporting and input validation.
- Automated backend tests.

**Frontend**
- React and TypeScript dashboard with city and date-range selection.
- Interactive daily temperature and threshold charts.
- Annual heatwave-frequency chart.
- Summary cards for event count, longest duration, peak temperature, and average duration.
- Heatwave event table and data-quality information.

**Current backend test status:** 22 passing tests.

### Planned

- Persistent storage and caching using a NoSQL database.
- Additional climate hazard types and trend-analysis capabilities.
- Downloadable analysis reports.
- Deployment of the frontend and backend.

## Technology Stack

### Backend

- Python
- FastAPI
- HTTPX
- Pytest

### Frontend

- React
- TypeScript
- Vite
- Recharts
- Lucide React

### Data Source

- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)

### Planned Database

- MongoDB

## Current API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/weather-preview` | Retrieve historical daily maximum temperatures for a coordinate and date range |
| GET | `/api/analyze` | Calculate heatwave thresholds, detect events, and return analysis summaries |

Interactive API documentation is available at `/docs` while the backend is running locally.

## Heatwave Detection Approach

The detector identifies a heatwave when daily maximum temperatures exceed their corresponding thresholds for at least three consecutive calendar days. The minimum duration is configurable.

The detector:

- Requires each observation to include a date, maximum temperature, and threshold.
- Uses a strict greater-than comparison: the temperature must exceed the threshold.
- Ends a qualifying run when the temperature or threshold is missing.
- Ends a run when a calendar day is missing.
- Returns the event's start date, end date, duration, peak temperature, and mean temperature excess.

A single day exceeding its threshold does not qualify as a heatwave when the minimum duration is three days.

## Temperature Threshold Method

The analysis service calculates calendar-day-specific percentile thresholds from historical baseline observations.

The default methodology uses:

- **Baseline period:** January 1, 1991, through December 31, 2020.
- **Percentile:** 95th percentile.
- **Moving window:** Five calendar days, consisting of the target day and two days on either side.
- **Percentile calculation:** Linear interpolation.
- **Missing temperatures:** Excluded from threshold calculations.
- **Minimum valid samples:** 30 observations per target date by default.

The percentile, moving-window size, and minimum consecutive heatwave duration can be configured through the analysis endpoint.

These settings define the project's current analytical method; they may be refined as the application develops.

## Analysis Results

The `/api/analyze` endpoint returns:

- Region coordinates and analysis period.
- Historical baseline period and methodology settings.
- Data-quality information, including missing analysis dates.
- Total detected heatwave events.
- Annual heatwave frequency.
- Average and longest event durations.
- Individual heatwave event details.
- Daily observations with their calculated thresholds.

### Annual Frequency Convention

Each heatwave event is counted in the calendar year in which its **start date** falls. If an event crosses December 31, it is counted in the year it started, not split between years.

Annual frequency represents the number of detected events beginning in each year of the requested analysis period.

## Local Development

### Prerequisites

Python 3.10 or later

Node.js 20 or a compatible supported version

npm

Git

### 1. Clone the repository

```powershell
git clone https://github.com/Vvekd123/climate-hazard-trend-analyzer.git
cd climate-hazard-trend-analyzer
```

### 2. Set up the backend

From the repository root, run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Start the backend

From the `backend` directory, run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open these URLs while the backend is running:

- Health check: http://127.0.0.1:8000/api/health
- Weather preview: http://127.0.0.1:8000/api/weather-preview
- Interactive API documentation: http://127.0.0.1:8000/docs

Use the interactive API documentation to test `/api/analyze` and configure the analysis coordinates, dates, baseline, percentile, moving window, and minimum event duration.

### 4. Run tests

From the `backend` directory, run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The current backend test suite contains 22 passing tests.

## Project Structure

```text
climate-hazard-trend-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

## Current Limitations

- The current implementation focuses on heatwave analysis; other climate hazards are not yet implemented.
- Historical weather data is retrieved from the external Open-Meteo Archive API.
- Persistent caching and NoSQL storage are planned.
- Advanced statistical trend analysis and downloadable reports are planned.
- Deployment of the frontend and backend is pending verification.

## License

To be determined.

## AI Tools and Usage Disclosure

AI tools were used as development assistance for exploring implementation approaches, debugging, reviewing code, and improving project documentation.

The application code, analytical methods, and outputs should be reviewed and tested by the developer. AI-generated suggestions are not treated as a substitute for verification or understanding of the implementation.