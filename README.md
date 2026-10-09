# ShopPulse

End-to-end e-commerce data pipeline: Airflow ingests raw data, dbt models it in BigQuery into tested tables, a churn model trains on the result, and a dashboard reads the output.

## Status

Day 1 — repo scaffold in progress.

## Stack

- **Warehouse:** BigQuery (sandbox)
- **Transformation:** dbt Core + dbt-bigquery
- **Orchestration:** Apache Airflow via Astro CLI (Docker)
- **ML:** Python, pandas, scikit-learn
- **CI:** GitHub Actions (ruff, sqlfluff, pytest)
- **Dashboard:** Looker Studio

## Data sources

- `bigquery-public-data.thelook_ecommerce` — TheLook eCommerce (BigQuery public dataset)
- [Nager.Date public holidays API](https://nagerholidays.com/api) — ingested via Airflow

## Repo layout

- `dags/` — Airflow DAGs
- `dbt/` — dbt project (sources, staging, marts)
- `ml/` — churn feature training script
- `tests/` — pytest tests for the API loader and feature logic

## Setup (Day 1)

1. Create a GCP project, enable BigQuery sandbox mode.
2. Create a service account with BigQuery roles, download its key — **never commit it** (see `.gitignore`).
3. Install Docker Desktop and the [Astro CLI](https://www.astronomer.io/docs/astro/cli/install-cli/).
4. From `ShopPulse/`, run `astro dev init` (this will add Airflow project files) then `astro dev start`.
5. Confirm the Airflow UI loads at `localhost:8080` and you can query `thelook_ecommerce.orders` in the BigQuery console.

## Design decisions

_To be filled in as the pipeline is built._

## What's next

See the 7-day build plan for the full day-by-day checklist.
