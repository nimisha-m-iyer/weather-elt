CREATE TABLE IF NOT EXISTS weather_hourly (
    city                  TEXT             NOT NULL,
    hour                  TIMESTAMP        NOT NULL,
    temperature_2m        DOUBLE PRECISION NOT NULL,
    relative_humidity_2m  DOUBLE PRECISION NOT NULL,
    precipitation         DOUBLE PRECISION NOT NULL,
    wind_speed_10m        DOUBLE PRECISION NOT NULL,
    loaded_at             TIMESTAMPTZ      NOT NULL DEFAULT now(),
    PRIMARY KEY (city, hour)
);

CREATE TABLE IF NOT EXISTS rejected_rows (
    id         BIGSERIAL   PRIMARY KEY,
    data_date  DATE        NOT NULL,
    city       TEXT,
    hour       TEXT,
    reason     TEXT        NOT NULL,
    raw_row    JSONB       NOT NULL,
    loaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rejected_date ON rejected_rows (data_date);