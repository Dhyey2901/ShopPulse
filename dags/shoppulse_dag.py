import os
from datetime import UTC, datetime

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task
from google.cloud import bigquery

from include.holidays import fetch_holidays

GCP_PROJECT = os.environ.get("DBT_GCP_PROJECT", "shoppulse-511205")
GCP_KEYFILE = os.path.join(
    "/usr/local/airflow/gcp-keys",
    os.environ.get("GCP_KEY_FILENAME", ""),
)
RAW_DATASET = "raw"
HOLIDAYS_TABLE = f"{GCP_PROJECT}.{RAW_DATASET}.holidays"
COUNTRY_CODE = "AU"
# TheLook order data starts in 2019 and keeps generating up to "today",
# so pull one year ahead to stay covered as new orders land.
HOLIDAY_YEARS = range(2019, datetime.now(UTC).year + 2)

HOLIDAYS_SCHEMA = [
    bigquery.SchemaField("date", "DATE"),
    bigquery.SchemaField("local_name", "STRING"),
    bigquery.SchemaField("name", "STRING"),
    bigquery.SchemaField("country_code", "STRING"),
    bigquery.SchemaField("year", "INTEGER"),
]


@dag(
    dag_id="shoppulse_pipeline",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["shoppulse"],
    default_args={"retries": 2},
)
def shoppulse_pipeline():
    @task
    def ingest_holidays():
        client = bigquery.Client.from_service_account_json(
            GCP_KEYFILE, project=GCP_PROJECT
        )
        client.create_dataset(
            bigquery.Dataset(f"{GCP_PROJECT}.{RAW_DATASET}"), exists_ok=True
        )

        rows = []
        for year in HOLIDAY_YEARS:
            rows.extend(fetch_holidays(year, COUNTRY_CODE))

        # BigQuery Sandbox mode (no billing account) disallows DML, so a
        # per-year DELETE+INSERT isn't possible here. Instead, every run
        # pulls the full year range fresh and overwrites the whole table
        # in one WRITE_TRUNCATE load job — same idempotency guarantee
        # (a rerun always lands at the same end state, never duplicates),
        # just at table granularity instead of per-year.
        job = client.load_table_from_json(
            rows,
            HOLIDAYS_TABLE,
            job_config=bigquery.LoadJobConfig(
                schema=HOLIDAYS_SCHEMA,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            ),
        )
        job.result()

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "cd /usr/local/airflow/dbt && "
            f"DBT_GCP_PROJECT={GCP_PROJECT} "
            f"DBT_GCP_DATASET={os.environ.get('DBT_GCP_DATASET', 'shoppulse_dev')} "
            f"DBT_GCP_KEYFILE={GCP_KEYFILE} "
            "DBT_PROFILES_DIR=/usr/local/airflow/dbt/profiles "
            "dbt build"
        ),
    )

    train_churn_model = BashOperator(
        task_id="train_churn_model",
        bash_command=(
            "cd /usr/local/airflow && "
            f"DBT_GCP_PROJECT={GCP_PROJECT} "
            f"DBT_GCP_DATASET={os.environ.get('DBT_GCP_DATASET', 'shoppulse_dev')} "
            f"DBT_GCP_KEYFILE={GCP_KEYFILE} "
            "python ml/train.py"
        ),
    )

    ingest_holidays() >> dbt_build >> train_churn_model


shoppulse_pipeline()
