# Weather ELT Pipeline

A daily pipeline that pulls hourly weather for five Indian cities from the
Open-Meteo API, validates it, and loads it into PostgreSQL. Orchestrated by
Airflow, packaged with Docker, tested with GitHub Actions.

![CI](https://github.com/YOUR-USERNAME/weather-elt/actions/workflows/ci.yml/badge.svg)

## What it does
(3 to 4 lines: extract, save raw JSON, validate, upsert, SQL summary, quality checks.)

## Architecture
(Paste the diagram from Phase 1, or draw one at excalidraw.com and save in docs/images.)

## Tech stack
Python, PostgreSQL, SQL (views, window functions), Airflow, Docker Compose, GitHub Actions, pytest

## Quick start
1. Install Docker Desktop and Python 3.12+
2. `git clone https://github.com/YOUR-USERNAME/weather-elt.git && cd weather-elt`
3. `python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt`
4. `docker compose up -d`
5. Airflow UI: http://localhost:8080 (user `admin`, password via
   `docker compose exec airflow cat /opt/airflow/standalone_admin_password.txt`)
6. Run a day by hand: the four `python -m src...` commands

## Screenshots
(Green Grid, red Grid, a rejected_rows query result.)

## Design decisions
- **Why ELT?** Load first, transform in SQL: the database is built for it
- **Why save raw JSON?** Replay after a bug or API change without re-calling the API
- **Why upsert on (city, hour)?** Reruns and backfills never duplicate rows
- **Why a rejected table?** Bad data is quarantined with a reason, not silently dropped
- **Why fail the DAG on a check?** A red run beats a green run with wrong data
- **Why standalone Airflow?** Simple for a local project; production would use separate scheduler, workers and a proper metadata DB

## Data quality checks
(The three rules, plus the real example: a 400.9 °C reading from the API caught by validation.)

## Testing
`pytest` runs validation and check logic; GitHub Actions runs it on every push.

## Limitations and next steps
- The API serves limited history for this endpoint
- Tests don't cover the database code (could add integration tests with a Postgres service in CI)
- Possible: dashboards, alerts on failure, more cities