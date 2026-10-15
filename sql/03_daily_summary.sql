CREATE TABLE IF NOT EXISTS daily_city_summary (
    city              TEXT          NOT NULL,
    obs_date          DATE          NOT NULL,
    min_temp_c        NUMERIC(5,2)  NOT NULL,
    max_temp_c        NUMERIC(5,2)  NOT NULL,
    avg_temp_c        NUMERIC(5,2)  NOT NULL,
    total_rain_mm     NUMERIC(7,2)  NOT NULL,
    avg_humidity_pct  NUMERIC(5,2)  NOT NULL,
    avg_wind_kmh      NUMERIC(6,2)  NOT NULL,
    hours_recorded    INTEGER       NOT NULL,
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    PRIMARY KEY (city, obs_date)
);

CREATE OR REPLACE VIEW daily_temp_change AS
SELECT
    city,
    obs_date,
    avg_temp_c,
    LAG(avg_temp_c)  OVER w                          AS prev_avg_temp_c,
    ROUND(avg_temp_c - LAG(avg_temp_c) OVER w, 2)    AS temp_change_c,
    obs_date - LAG(obs_date) OVER w                  AS days_since_prev
FROM daily_city_summary
WINDOW w AS (PARTITION BY city ORDER BY obs_date);