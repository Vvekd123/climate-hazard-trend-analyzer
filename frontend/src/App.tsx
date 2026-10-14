import { useState } from "react";
import {
  Activity,
  CalendarDays,
  CloudSun,
  MapPin,
  RefreshCw,
  Thermometer,
  TrendingUp,
  Waves,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const regions = {
  Bengaluru: { latitude: 12.9716, longitude: 77.5946 },
  Delhi: { latitude: 28.6139, longitude: 77.209 },
  Mumbai: { latitude: 19.076, longitude: 72.8777 },
  Chennai: { latitude: 13.0827, longitude: 80.2707 },
};

type RegionName = keyof typeof regions;

type DailyObservation = {
  date: string;
  temperature_max: number | null;
  threshold: number;
};

type AnalysisEvent = {
  start_date: string;
  end_date: string;
  duration_days: number;
  peak_temperature_c: number;
  mean_excess_c: number;
};

type AnalysisResponse = {
  region: { latitude: number; longitude: number };
  analysis_period: { start_date: string; end_date: string };
  data_quality: {
    analysis_records_received: number;
    missing_analysis_dates: string[];
    missing_analysis_date_count: number;
  };
  summary: {
    total_events: number;
    annual_frequency: Record<string, number>;
    average_duration_days: number;
    longest_event_days: number;
  };
  events: AnalysisEvent[];
  daily_observations: DailyObservation[];
};

type TemperatureChartPoint = {
  date: string;
  fullDate: string;
  temperature: number | null;
  threshold: number;
};

function formatDate(value: string) {
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function TemperatureTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: TemperatureChartPoint }>;
}) {
  if (!active || !payload?.length) return null;

  const point = payload[0].payload;

  return (
    <div className="chart-tooltip">
      <p className="tooltip-date">{formatDate(point.fullDate)}</p>
      <div className="tooltip-row">
        <span className="tooltip-dot temperature-dot" />
        <span>Maximum temperature</span>
        <strong>
          {point.temperature === null
            ? "Missing"
            : `${point.temperature.toFixed(1)} °C`}
        </strong>
      </div>
      <div className="tooltip-row">
        <span className="tooltip-dot threshold-dot" />
        <span>95th-percentile threshold</span>
        <strong>{point.threshold.toFixed(2)} °C</strong>
      </div>
    </div>
  );
}

function App() {
  const [region, setRegion] = useState<RegionName>("Bengaluru");
  const [startDate, setStartDate] = useState("2020-05-01");
  const [endDate, setEndDate] = useState("2020-05-07");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleAnalyze() {
    if (!startDate || !endDate) {
      setError("Please select both a start date and an end date.");
      return;
    }

    if (startDate > endDate) {
      setError("Start date must not be after end date.");
      return;
    }

    const coordinates = regions[region];
    const params = new URLSearchParams({
      latitude: String(coordinates.latitude),
      longitude: String(coordinates.longitude),
      start_date: startDate,
      end_date: endDate,
    });

    setLoading(true);
    setError("");

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/analyze?${params.toString()}`,
      );

      if (!response.ok) {
        const body: { detail?: string } | null = await response
          .json()
          .catch(() => null);
        throw new Error(
          body?.detail ?? `Analysis failed with status ${response.status}.`,
        );
      }

      const result: AnalysisResponse = await response.json();
      setAnalysis(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message} Check that the backend is running and reachable.`
          : "Unable to retrieve climate analysis. Check the backend connection.",
      );
    } finally {
      setLoading(false);
    }
  }

  const observations = analysis?.daily_observations ?? [];

  const chartData: TemperatureChartPoint[] = observations.map((item) => ({
    date: new Date(`${item.date}T00:00:00`).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
    }),
    fullDate: item.date,
    temperature: item.temperature_max,
    threshold: item.threshold,
  }));

  const annualFrequencyData = analysis
    ? Object.entries(analysis.summary.annual_frequency)
        .map(([year, events]) => ({ year, events }))
        .sort((a, b) => Number(a.year) - Number(b.year))
    : [];

  const peakTemperature = observations.reduce<number | null>(
    (maximum, item) =>
      item.temperature_max === null
        ? maximum
        : maximum === null
          ? item.temperature_max
          : Math.max(maximum, item.temperature_max),
    null,
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><CloudSun size={24} /></div>
          <div>
            <h2>ClimateScope</h2>
            <p>Hazard Intelligence</p>
          </div>
        </div>

        <div className="nav-label">WORKSPACE</div>
        <div className="nav-item active">
          <Activity size={18} /> Climate overview
        </div>
        <div className="nav-item">
          <TrendingUp size={18} /> Trend analysis
        </div>
        <div className="nav-item">
          <MapPin size={18} /> Regions
        </div>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          Historical weather analysis
          <p>Powered by Open-Meteo</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">CLIMATE MONITORING / OVERVIEW</p>
            <h1>Climate hazard analyzer</h1>
            <p className="subtitle">
              Explore historical climate extremes and identify heatwave patterns.
            </p>
          </div>
          <div className="live-badge"><span /> Historical data</div>
        </header>

        <section className="filters panel">
          <div className="filter-field">
            <label htmlFor="region">Region</label>
            <select
              id="region"
              value={region}
              onChange={(event) => setRegion(event.target.value as RegionName)}
            >
              <option value="Bengaluru">Bengaluru, India</option>
              <option value="Delhi">Delhi, India</option>
              <option value="Mumbai">Mumbai, India</option>
              <option value="Chennai">Chennai, India</option>
            </select>
          </div>

          <div className="filter-field">
            <label htmlFor="startDate">Start date</label>
            <input
              id="startDate"
              type="date"
              value={startDate}
              max={endDate}
              onChange={(event) => setStartDate(event.target.value)}
            />
          </div>

          <div className="filter-field">
            <label htmlFor="endDate">End date</label>
            <input
              id="endDate"
              type="date"
              value={endDate}
              min={startDate}
              onChange={(event) => setEndDate(event.target.value)}
            />
          </div>

          <div className="filter-field">
            <label>Hazard type</label>
            <div className="hazard-select"><Thermometer size={17} /> Heatwave</div>
          </div>

          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? "spin" : ""} />
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </section>

        {error && (
          <div className="error-banner" role="alert">
            <strong>Analysis failed:</strong> {error}
          </div>
        )}

        <section className="section-heading">
          <div>
            <h2>Analysis overview</h2>
            <p>
              {analysis
                ? `${formatDate(analysis.analysis_period.start_date)} – ${formatDate(analysis.analysis_period.end_date)}`
                : "Choose a region and date range, then select Analyze."}
            </p>
          </div>
          <div className="period-label"><CalendarDays size={15} /> Selected period</div>
        </section>

        <section className="stats-grid">
          <article className="stat-card panel">
            <div className="stat-top"><span>Total heatwaves</span><Activity /></div>
            <div className="stat-value">{analysis?.summary.total_events ?? "—"}</div>
            <p className="stat-note">Detected in selected period</p>
          </article>

          <article className="stat-card panel">
            <div className="stat-top"><span>Longest duration</span><CalendarDays /></div>
            <div className="stat-value">
              {analysis ? analysis.summary.longest_event_days : "—"} <small>days</small>
            </div>
            <p className="stat-note">Longest qualifying event</p>
          </article>

          <article className="stat-card panel">
            <div className="stat-top"><span>Peak temperature</span><Thermometer /></div>
            <div className="stat-value">
              {peakTemperature === null ? "—" : peakTemperature.toFixed(1)}<small> °C</small>
            </div>
            <p className="stat-note">Highest observed temperature</p>
          </article>

          <article className="stat-card panel">
            <div className="stat-top"><span>Average duration</span><TrendingUp /></div>
            <div className="stat-value">
              {analysis ? analysis.summary.average_duration_days : "—"}<small> days</small>
            </div>
            <p className="stat-note">Across detected events</p>
          </article>
        </section>

        <section className="chart-panel panel">
          <div className="chart-heading">
            <div>
              <h2>Daily temperature vs threshold</h2>
              <p>Daily maximum temperature compared with the 95th-percentile threshold</p>
            </div>
            <div className="chart-unit">Temperature · °C</div>
          </div>

          <div className="chart-container">
            {analysis && chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 12, right: 18, left: 4, bottom: 4 }}>
                  <CartesianGrid stroke="#e8eee9" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="date"
                    tickLine={false}
                    axisLine={false}
                    interval="preserveStartEnd"
                    minTickGap={40}
                    tickMargin={10}
                  />
                  <YAxis
                    domain={["auto", "auto"]}
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    width={42}
                    tickFormatter={(value: number) => `${value}°`}
                  />
                  <Tooltip content={<TemperatureTooltip />} />
                  <Legend verticalAlign="top" height={34} />
                  <Line
                    type="monotone"
                    dataKey="temperature"
                    name="Maximum temperature"
                    stroke="#287d6b"
                    strokeWidth={2}
                    connectNulls={false}
                    dot={false}
                    activeDot={{ r: 4 }}
                    isAnimationActive={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="threshold"
                    name="95th-percentile threshold"
                    stroke="#df9250"
                    strokeWidth={2}
                    strokeDasharray="6 4"
                    dot={false}
                    activeDot={{ r: 4 }}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-chart">
                {loading
                  ? "Fetching historical data and calculating thresholds..."
                  : "Run an analysis to display real historical temperatures."}
              </div>
            )}
          </div>
        </section>

        {analysis && (
          <section className="chart-panel panel">
            <div className="chart-heading">
              <div>
                <h2>Annual heatwave frequency</h2>
                <p>Detected events grouped by the calendar year in which each event started</p>
              </div>
              <div className="chart-unit">Events · year</div>
            </div>
            <div className="chart-container">
              {annualFrequencyData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={annualFrequencyData} margin={{ top: 12, right: 18, left: 4, bottom: 4 }}>
                    <CartesianGrid stroke="#e8eee9" strokeDasharray="3 3" vertical={false} />
                    <XAxis
                      dataKey="year"
                      tickLine={false}
                      axisLine={false}
                      minTickGap={40}
                      interval="preserveStartEnd"
                      tickMargin={10}
                    />
                    <YAxis
                      allowDecimals={false}
                      domain={[0, "auto"]}
                      tickLine={false}
                      axisLine={false}
                      width={42}
                    />
                    <Tooltip
                      formatter={(value) => [value, "Heatwave events"]}
                      labelFormatter={(label) => `Year ${label}`}
                      contentStyle={{
                        borderRadius: 10,
                        border: "1px solid #e3ebe5",
                        boxShadow: "0 8px 24px rgba(25, 59, 47, 0.08)",
                        fontSize: 12,
                      }}
                    />
                    <Bar
                      dataKey="events"
                      name="Heatwave events"
                      fill="#287d6b"
                      radius={[5, 5, 0, 0]}
                      maxBarSize={28}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-chart">No annual frequency data is available for this period.</div>
              )}
            </div>
          </section>
        )}

        {analysis && (
          <section className="chart-panel panel events-panel">
            <div className="chart-heading">
              <div>
                <h2>Data quality and detected events</h2>
                <p>
                  {analysis.data_quality.analysis_records_received} daily records received. {" "}
                  {analysis.data_quality.missing_analysis_date_count} missing dates.
                </p>
              </div>
            </div>

            {analysis.data_quality.missing_analysis_date_count > 0 && (
              <p className="warning-text">
                Missing dates: {analysis.data_quality.missing_analysis_dates.join(", ")}
              </p>
            )}

            {analysis.events.length === 0 ? (
              <p className="empty-events">No qualifying heatwave events were detected in this period.</p>
            ) : (
              <div className="table-wrapper">
                <table className="events-table">
                  <thead>
                    <tr>
                      <th>Start date</th>
                      <th>End date</th>
                      <th>Duration</th>
                      <th>Peak temperature</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.events.map((event) => (
                      <tr key={`${event.start_date}-${event.end_date}`}>
                        <td>{formatDate(event.start_date)}</td>
                        <td>{formatDate(event.end_date)}</td>
                        <td>{event.duration_days} days</td>
                        <td>{event.peak_temperature_c.toFixed(1)} °C</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        <footer className="dashboard-footer">
          <Waves size={16} />
          <span>ClimateScope · Historical climate analysis</span>
          <span>Data source: Open-Meteo Archive API</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
