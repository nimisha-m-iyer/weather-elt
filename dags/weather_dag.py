from datetime import datetime, timedelta

from airflow import DAG # type: ignore
from airflow.operators.bash import BashOperator # type: ignore

PROJECT = "/opt/airflow/project"


def run_module(task_id, module):
    """One task = run 'python -m src.<module> --date <the day to process>'."""
    return BashOperator(
        task_id=task_id,
        bash_command="cd " + PROJECT + " && python -m src." + module + " --date {{ ds }}",
    )


with DAG(
    dag_id="weather_elt",
    description="Daily weather ELT: extract, validate+load, transform, check",
    start_date=datetime(2026, 10, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=2)},
    tags=["weather"],
) as dag:
    extract = run_module("extract", "extract")
    validate_and_load = run_module("validate_and_load", "load")
    transform = run_module("transform", "transform")
    quality_checks = run_module("quality_checks", "checks")

    extract >> validate_and_load >> transform >> quality_checks