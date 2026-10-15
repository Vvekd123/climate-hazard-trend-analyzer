# Weather Source Comparison

Audit date: 2026-10-15

## Method

Requested Bengaluru coordinates 12.972 N, 77.595 E. Compared NASA POWER daily `T2M_MAX` against Open-Meteo Archive `temperature_2m_max` for May 1-10, 2020, then repeated once for calendar year 2020. All requests used UTC. Dates were joined exactly; no values were imputed. Difference is NASA minus Open-Meteo in deg C. MAE is the mean absolute paired difference. Pearson r is descriptive only and does not establish accuracy or agreement.

Requests:

- NASA POWER: `https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M_MAX&community=RE&longitude=77.595&latitude=12.972&start=20200501&end=20200510&format=JSON&time-standard=UTC`
- Open-Meteo default archive: `https://archive-api.open-meteo.com/v1/archive?latitude=12.972&longitude=77.595&start_date=2020-05-01&end_date=2020-05-10&daily=temperature_2m_max&timezone=UTC`
- Open-Meteo ERA5-Land: same Open-Meteo request with `&models=era5_land`

## Returned Metadata and Coverage

| Source | Returned coordinates (longitude, latitude) | Elevation | Units | Time | Valid May pairs | Valid 2020 pairs |
|---|---:|---:|---|---|---:|---:|
| NASA POWER | 77.595, 12.972 | 841.72 m | C | UTC | 10/10 | 366/366 |
| Open-Meteo default archive | 77.563640, 12.970123 | 906 m | deg C | GMT, UTC offset 0 | 10/10 | 366/366 |
| Open-Meteo ERA5-Land | 77.600006, 13.000000 | 906 m | deg C | GMT, UTC offset 0 | 10/10 | 366/366 |

NASA's response reported `T2M_MAX` units C, `time_standard` UTC, fill value -999, and returned the requested horizontal coordinate. No fill values occurred in either sampled period. Each Open-Meteo response returned 10 unique dates for May and 366 unique dates for 2020; all dates aligned with NASA. Open-Meteo reports snapped grid coordinates and elevation that differ from NASA's metadata.

## May 1-10 Daily Pairs

| Date | NASA POWER | Open-Meteo default | NASA - default | Open-Meteo ERA5-Land | NASA - ERA5-Land |
|---|---:|---:|---:|---:|---:|
| 2020-05-01 | 35.30 | 32.80 | +2.50 | 32.40 | +2.90 |
| 2020-05-02 | 35.77 | 33.10 | +2.67 | 32.70 | +3.07 |
| 2020-05-03 | 35.13 | 33.40 | +1.73 | 33.50 | +1.63 |
| 2020-05-04 | 37.13 | 33.70 | +3.43 | 33.00 | +4.13 |
| 2020-05-05 | 36.36 | 34.20 | +2.16 | 33.40 | +2.96 |
| 2020-05-06 | 34.72 | 34.80 | -0.08 | 33.20 | +1.52 |
| 2020-05-07 | 34.05 | 34.30 | -0.25 | 32.50 | +1.55 |
| 2020-05-08 | 34.15 | 33.80 | +0.35 | 32.70 | +1.45 |
| 2020-05-09 | 36.72 | 34.80 | +1.92 | 33.90 | +2.82 |
| 2020-05-10 | 35.34 | 35.20 | +0.14 | 34.20 | +1.14 |

## Metrics

| Period and comparator | Pairs | MAE (deg C) | Mean signed difference (deg C) | Maximum absolute difference (deg C) | Pearson r |
|---|---:|---:|---:|---:|---:|
| May 1-10, Open-Meteo default | 10 | 1.5230 | +1.4570 | 3.4300 | -0.0136 |
| May 1-10, Open-Meteo ERA5-Land | 10 | 2.3170 | +2.3170 | 4.1300 | 0.3784 |
| Calendar year 2020, Open-Meteo default | 366 | 1.6872 | +1.3117 | 5.5600 | 0.9293 |
| Calendar year 2020, Open-Meteo ERA5-Land | 366 | 2.1350 | +1.9013 | 5.9600 | 0.9205 |

The ten-day result reproduces the README's ERA5-Land values when rounded (MAE approximately 2.32 deg C; maximum absolute difference 4.13 deg C). The year sample has substantially higher temporal correlation, but correlation does not establish small error or identify either product as ground truth. The datasets use different grids, elevations, source models, and potentially different daily aggregation. This is a consistency comparison, not station validation or an official acceptance test.
