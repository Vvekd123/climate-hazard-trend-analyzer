# Climate Hazard Trend Analyzer

A full-stack climate analysis application that retrieves historical weather data, detects heatwave events, and visualizes climate hazard trends using a React dashboard and Python FastAPI backend.

## Live Application

- **Frontend:** https://climate-hazard-trend-analyzer-six.vercel.app/
- **Backend API:** https://climate-hazard-trend-analyzer-ckff.onrender.com
- **Interactive API documentation:** https://climate-hazard-trend-analyzer-ckff.onrender.com/docs
- **Health check:** https://climate-hazard-trend-analyzer-ckff.onrender.com/api/health
- **GitHub repository:** https://github.com/Vvekd123/climate-hazard-trend-analyzer

The frontend is hosted on Vercel and the backend on Render. MongoDB Atlas is used for weather-data caching when correctly configured.

## Features

### Backend

- FastAPI endpoints for health checks, weather previews, and climate analysis.
- Historical daily maximum-temperature retrieval from NASA POWER.
- MongoDB-backed caching of weather observations.
- Handling of missing cached dates and partial cache hits.
- Chunking of large date ranges into smaller weather API requests.
- Handling of upstream API rate limits, including HTTP 429 responses.
- Calendar-day-specific 95th-percentile temperature thresholds.
- Configurable moving-window percentile calculations.
- Heatwave detection based on consecutive days exceeding their thresholds.
- Annual heatwave-frequency summaries and trend analysis.
- Missing-data reporting and input validation.
- Automated tests for climate calculations, heatwave detection, and weather-cache behavior.

### Frontend

- React and TypeScript dashboard.
- Geographic region selection and date-range filters.
- Heatwave as the selected hazard type.
- Daily temperature-versus-threshold visualization.
- Annual heatwave-frequency visualization.
- Summary cards for event count, longest duration, peak temperature, and average duration.
- Heatwave event details and data-quality information.
- Integration with the deployed FastAPI backend.

The dashboard displays analysis results after the user selects the required inputs and runs an analysis.

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- Recharts
- Lucide React

### Backend
- Python
- FastAPI
- HTTPX
- Uvicorn
- Pytest

### Database
- MongoDB Atlas

### Weather Data
- [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) for independent comparison and validation

## Architecture

```text
User
 |
 v
React + TypeScript Dashboard
(Vercel)
 |
 | HTTPS API requests
 v
FastAPI Backend
(Render)
 |
 +----> NASA POWER Daily API
 |       Historical daily maximum temperatures
 |
 +----> MongoDB Atlas
         Cached weather observations
```

The backend retrieves historical temperature observations, checks the weather cache, calculates percentile thresholds, detects qualifying heatwave events, and returns analysis results as JSON. The frontend displays the returned results through charts, summary cards, and event details.

Weather data is retrieved from an external API when it is not available in the cache. MongoDB connectivity and cache failures must be handled explicitly; the application should not silently claim data was cached when persistence failed.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/weather-preview` | Retrieve historical daily maximum temperatures |
| GET | `/api/analyze` | Calculate thresholds, detect heatwaves, and return analysis summaries |

See `/docs` on the deployed backend for endpoint parameters and response schemas.

## Heatwave Detection

A heatwave is defined as at least three consecutive calendar days on which the daily maximum temperature exceeds the applicable threshold.

The detector:

- Compares each day's maximum temperature against its corresponding threshold.
- Uses a strict greater-than comparison.
- Requires a configurable minimum number of consecutive days.
- Ends a qualifying run when the temperature or threshold is missing.
- Ends a run when a calendar day is missing.
- Returns event dates, duration, peak temperature, and mean temperature excess.

A single hot day does not qualify as a heatwave when the minimum duration is three days.

## Temperature Threshold Methodology

The application uses calendar-day-specific percentile thresholds calculated from historical baseline observations.

Default methodology:

- **Baseline period:** January 1, 1991, through December 31, 2020.
- **Percentile:** 95th percentile.
- **Moving window:** Five calendar days, including the target day and two days on either side.
- **Percentile calculation:** Linear interpolation.
- **Missing baseline temperatures:** Excluded from percentile calculations.
- **Minimum valid baseline samples:** 30 observations per target calendar day by default.

The percentile, moving-window size, and minimum heatwave duration can be configured through the analysis endpoint.

The baseline represents the historical reference period used to identify unusually hot conditions. It does not imply that the underlying weather observations have been independently verified against station measurements.

## Trend Analysis

The application summarizes annual heatwave frequency and event duration to help users explore how detected events vary over time.

Annual frequency counts an event in the calendar year in which it begins. An event crossing December 31 is counted in its start year rather than split across two years.

Trend estimates use only year buckets whose requested analysis period covers January 1 through December 31, excluding partial endpoint years, and require at least five such years. Missing dates and measurements within those years are reported but do not exclude the year from the regression, so they can affect annual counts. Estimates are descriptive ordinary-least-squares slopes, not statistical significance tests. Interpret them in the context of data completeness, baseline selection, and the limitations of gridded weather data; a trend in detected events is not, by itself, proof of causation.

## Data Quality and Validation

Analysis responses distinguish calendar dates absent from the returned observations (`missing_analysis_date_count`) from returned dates without a valid maximum-temperature measurement (`missing_temperature_date_count`). Missing values, NASA's -999 fill value, and non-finite temperatures are represented as null and are not used as temperatures. Malformed non-numeric values retain the existing upstream-error response path.

The application also checks valid inputs and consecutive calendar-day requirements. Missing temperature measurements break a heatwave run.

During development, NASA POWER data was compared with Open-Meteo historical temperature data for Bengaluru for May 1–10, 2020.

The comparison against Open-Meteo's ERA5-Land dataset showed a mean absolute difference of approximately 2.32°C and a maximum absolute difference of approximately 4.13°C over the ten-day sample.

This is a preliminary comparison, not a complete accuracy validation. The sources use different gridded datasets and returned different grid coordinates. The discrepancy requires further investigation, ideally including longer-period comparisons and independent weather-station observations.

NASA POWER is therefore treated as the application's operational data source, but its absolute accuracy for the selected location has not been established by this limited comparison.

## Local Development

### Prerequisites

- Python 3.10 or later
- Node.js and npm
- Git
- A MongoDB Atlas connection if you want to test persistent weather caching locally

### 1. Clone the repository

```powershell
git clone https://github.com/Vvekd123/climate-hazard-trend-analyzer.git
cd climate-hazard-trend-analyzer
```

### 2. Set up the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Configure the MongoDB connection using the `MONGODB_URI` environment variable.

For local development, set it in your terminal or a local environment configuration that is excluded from Git. For example, in PowerShell:

```powershell
$env:MONGODB_URI = "your-mongodb-connection-string"
```

Never commit database credentials or connection strings to the repository. MongoDB Atlas must be configured and reachable for persistent weather caching.

### 3. Start the backend

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

Useful endpoints:

- Health check: http://127.0.0.1:8000/api/health
- Weather preview: http://127.0.0.1:8000/api/weather-preview
- Interactive documentation: http://127.0.0.1:8000/docs

Use the interactive documentation to inspect the analysis endpoint's supported parameters.

### 4. Run backend tests

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The current local test suite contains **55 tests**, covering climate analysis, threshold calculation, heatwave detection, and weather caching.

### 5. Set up the frontend

Open a second terminal at the repository root:

```powershell
cd frontend
npm install
```

Create `frontend/.env.local` with:

```env
VITE_API_BASE_URL=https://climate-hazard-trend-analyzer-ckff.onrender.com
```

For local backend development, use:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### 6. Start the frontend

From the `frontend` directory:

```powershell
npm run dev
```

Open the local URL printed by Vite, typically `http://localhost:5173`.

### 7. Build the frontend

From the `frontend` directory:

```powershell
npm run build
```

Vite generates the production build in `frontend/dist`.

## Deployment

The frontend and backend are deployed separately from the same GitHub repository.

### Vercel — Frontend

- Repository: `Vvekd123/climate-hazard-trend-analyzer`
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL`

### Render — Backend

- Repository: `Vvekd123/climate-hazard-trend-analyzer`
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Both services use free-tier hosting, subject to provider limits and availability.

## Current Limitations

- Heatwave analysis is implemented; drought and heavy-rainfall analysis are not currently supported.
- Historical temperatures come from gridded weather data and may differ from observations at individual weather stations.
- Cross-source comparison has been performed on a small sample and is not a complete accuracy assessment.
- The reliability of trend conclusions depends on data completeness, threshold methodology, and the selected analysis period.
- Map-based region selection and downloadable reports are potential future enhancements.
- Free hosting services may sleep after inactivity, increasing initial response times.

## Future Improvements

- Validate longer historical periods against independent weather products and station observations.
- Add more comprehensive cache observability and data-quality reporting.
- Add CSV export of heatwave events and annual summaries.
- Add map-based region selection.
- Explore additional climate hazards after validating the heatwave workflow.
- Evaluate additional statistical trend tests and uncertainty reporting.

## AI Tools and Usage Disclosure

AI tools, including ChatGPT, were used as development assistance for exploring implementation approaches, debugging, reviewing test failures, improving documentation, and investigating weather-data discrepancies.

The developer remains responsible for reviewing and testing the implementation, understanding the analytical methodology, and explaining the design decisions during the interview. AI-generated suggestions are not treated as proof of correctness without verification.

## License

No license has been selected for this repository. The project is publicly accessible on GitHub.
