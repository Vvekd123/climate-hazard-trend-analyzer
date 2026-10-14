# Climate Hazard Trend Analyzer

A full-stack web application for analyzing historical climate data, detecting heatwave events, and exploring temperature patterns using a React dashboard and Python FastAPI backend.

## Live Application

- **Frontend Dashboard:** https://climate-hazard-trend-analyzer-six.vercel.app/
- **Backend API:** https://climate-hazard-trend-analyzer-ckff.onrender.com
- **Interactive API Documentation:** https://climate-hazard-trend-analyzer-ckff.onrender.com/docs
- **Health Check:** https://climate-hazard-trend-analyzer-ckff.onrender.com/api/health

The frontend is hosted on Vercel, and the backend is hosted on Render. Both services use the same GitHub repository.

## Project Status

The React/TypeScript frontend and FastAPI backend are implemented and deployed. The backend test suite currently contains 22 passing tests.

### Implemented Features

**Backend**
- FastAPI endpoints for health checks, weather previews, and heatwave analysis.
- Historical daily maximum-temperature retrieval using the Open-Meteo Archive API.
- Calendar-day-specific 95th-percentile temperature thresholds.
- Configurable moving-window percentile calculations.
- Heatwave detection based on consecutive days exceeding their thresholds.
- Annual heatwave frequency and event-duration summaries.
- Missing-data reporting and input validation.
- Automated tests for heatwave detection, threshold calculations, and analysis behavior.

**Frontend**
- React and TypeScript dashboard.
- City selection and date-range filtering.
- Interactive daily temperature and threshold charts.
- Annual heatwave-frequency chart.
- Summary cards for event count, longest duration, peak temperature, and average duration.
- Heatwave event table and data-quality information.
- Integration with the deployed FastAPI backend.

**Current backend test status:** 22 passing tests.

### Planned Features

- Persistent weather-data caching.
- NoSQL database integration using MongoDB.
- Additional climate hazard types.
- Advanced statistical trend analysis.
- Downloadable analysis reports.

## Technology Stack

### Backend
- Python
- FastAPI
- HTTPX
- Uvicorn
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
- MongoDB Atlas

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
 | Historical weather requests
 v
Open-Meteo Archive API
```

The backend retrieves historical weather observations, calculates temperature thresholds, detects heatwave events, and returns analysis results as JSON. The frontend presents these results through interactive charts, summary cards, and an event table.

Persistent database storage and caching have not yet been implemented.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend health |
| GET | `/api/weather-preview` | Retrieve historical daily maximum temperatures |
| GET | `/api/analyze` | Calculate thresholds, detect heatwaves, and return analysis summaries |

Interactive API documentation is available at `/docs` on the deployed backend.

## Heatwave Detection Approach

The detector identifies a heatwave when daily maximum temperatures exceed their corresponding thresholds for at least three consecutive calendar days. The minimum duration is configurable.

The detector:
- Requires each observation to include a date, maximum temperature, and threshold.
- Uses a strict greater-than comparison.
- Ends a qualifying run when the temperature or threshold is missing.
- Ends a run when a calendar day is missing.
- Returns the event's start date, end date, duration, peak temperature, and mean temperature excess.

A single day exceeding its threshold does not qualify as a heatwave when the minimum duration is three days.

## Temperature Threshold Method

The analysis service calculates calendar-day-specific percentile thresholds using historical baseline observations.

Default methodology:

- **Baseline period:** January 1, 1991, through December 31, 2020.
- **Percentile:** 95th percentile.
- **Moving window:** Five calendar days, comprising the target day and two days on either side.
- **Percentile calculation:** Linear interpolation.
- **Missing temperatures:** Excluded from threshold calculations.
- **Minimum valid samples:** 30 observations per target date by default.

The percentile, moving-window size, and minimum consecutive heatwave duration can be configured through the analysis endpoint.

These settings describe the project's current analytical methodology and may be refined in future versions.

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

Each heatwave event is counted in the calendar year in which its start date falls. An event crossing December 31 is counted in the year it started, rather than being split between years.

Annual frequency represents the number of detected events beginning in each year of the requested analysis period.

## Local Development

### Prerequisites

- Python 3.10 or later
- Node.js 20 or a compatible supported version
- npm
- Git

### 1. Clone the Repository

```powershell
git clone https://github.com/Vvekd123/climate-hazard-trend-analyzer.git
cd climate-hazard-trend-analyzer
```

### 2. Set Up the Backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Start the Backend

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The backend will run at `http://127.0.0.1:8000`.

Available local endpoints:

- Health check: http://127.0.0.1:8000/api/health
- Weather preview: http://127.0.0.1:8000/api/weather-preview
- API documentation: http://127.0.0.1:8000/docs

Use the interactive API documentation to test `/api/analyze` and configure coordinates, dates, baseline settings, percentile, moving window, and minimum event duration.

### 4. Run Backend Tests

From the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The current backend test suite contains 22 tests.

### 5. Set Up the Frontend

Open a second terminal from the repository root:

```powershell
cd frontend
npm install
```

Create a `frontend/.env.local` file with the following variable to use the deployed backend during local frontend development:

```env
VITE_API_BASE_URL=https://climate-hazard-trend-analyzer-ckff.onrender.com
```

To use a locally running backend instead, set the value to `http://127.0.0.1:8000`.

### 6. Start the Frontend

From the `frontend` directory:

```powershell
npm run dev
```

Open the local URL printed by Vite, typically `http://localhost:5173`.

### 7. Build the Frontend for Production

From the `frontend` directory:

```powershell
npm run build
```

Vite generates the production build in `frontend/dist`.

## Deployment

The application uses a single GitHub repository with separate frontend and backend deployments.

### Frontend — Vercel
- Repository: `Vvekd123/climate-hazard-trend-analyzer`
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable: `VITE_API_BASE_URL`

### Backend — Render
- Repository: `Vvekd123/climate-hazard-trend-analyzer`
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Both services are currently deployed using their respective free plans, subject to provider limits and availability.

## Current Limitations

- The current implementation focuses on heatwave analysis; other climate hazards are not yet implemented.
- Historical weather observations are retrieved from the external Open-Meteo Archive API.
- Persistent caching and NoSQL database storage are planned.
- Advanced statistical trend analysis and downloadable reports are planned.
- Free hosting services may sleep after periods of inactivity, resulting in slower initial responses.

## AI Tools and Usage Disclosure

AI tools were used as development assistance for exploring implementation approaches, debugging, reviewing code, and improving project documentation.

The developer is responsible for reviewing and testing the implementation, understanding the analytical methods, and validating the outputs. AI-generated suggestions are not treated as a substitute for verification or understanding of the code.

## License

No license has been selected yet. The project is currently published as a public GitHub repository.