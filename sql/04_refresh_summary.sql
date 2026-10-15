INSERT INTO daily_city_summary (
    city, obs_date, min_temp_c, max_temp_c, avg_temp_c,
    total_rain_mm, avg_humidity_pct, avg_wind_kmh, hours_recorded
)
SELECT
    city,
    obs_date,
    MIN(temp_c),
    MAX(temp_c),
    ROUND(AVG(temp_c)::numeric, 2),
    ROUND(SUM(rain_mm)::numeric, 2),
    ROUND(AVG(humidity_pct)::numeric, 2),
    ROUND(AVG(wind_kmh)::numeric, 2),
    COUNT(*)
FROM stg_weather
WHERE obs_date = %(day)s
GROUP BY city, obs_date
ON CONFLICT (city, obs_date) DO UPDATE SET
    min_temp_c       = EXCLUDED.min_temp_c,
    max_temp_c       = EXCLUDED.max_temp_c,
    avg_temp_c       = EXCLUDED.avg_temp_c,
    total_rain_mm    = EXCLUDED.total_rain_mm,
    avg_humidity_pct = EXCLUDED.avg_humidity_pct,
    avg_wind_kmh     = EXCLUDED.avg_wind_kmh,
    hours_recorded   = EXCLUDED.hours_recorded,
    updated_at       = now();