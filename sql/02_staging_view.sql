CREATE OR REPLACE VIEW stg_weather AS
SELECT
    city,
    hour                      AS observed_at,   -- local time (Asia/Kolkata)
    hour::date                AS obs_date,
    temperature_2m            AS temp_c,
    relative_humidity_2m      AS humidity_pct,
    precipitation             AS rain_mm,
    wind_speed_10m            AS wind_kmh,
    loaded_at
FROM weather_hourly;