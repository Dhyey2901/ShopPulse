"""Train a churn classifier on ml_churn_features and write scores back to BigQuery.

Churn is defined in dbt (ml_churn_features.sql) as: no order in the last 90
days, snapshotted at CURRENT_DATE() for the whole table in one run. This
script trains on that same snapshot - it classifies current churn status
from RFM + category-mix features, it does not forecast a future event.
"""
import os
import sys

import pandas as pd
from google.cloud import bigquery
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

GCP_PROJECT = os.environ.get("DBT_GCP_PROJECT", "shoppulse-511205")
GCP_DATASET = os.environ.get("DBT_GCP_DATASET", "shoppulse_dev")
GCP_KEYFILE = os.environ.get("DBT_GCP_KEYFILE")

FEATURES_TABLE = f"{GCP_PROJECT}.{GCP_DATASET}.ml_churn_features"
SCORES_TABLE = f"{GCP_PROJECT}.{GCP_DATASET}.churn_scores"

# recency_days is deliberately excluded: is_churned is partly *defined* as
# recency_days > 90, so including it would let the model trivially learn
# that rule instead of a real predictive pattern (perfect-looking but
# meaningless precision/recall/ROC-AUC). frequency, monetary, and category
# mix are genuinely independent of the label.
NUMERIC_FEATURES = ["frequency", "monetary", "distinct_categories"]
CATEGORICAL_FEATURES = ["top_category"]


def get_client():
    if GCP_KEYFILE:
        return bigquery.Client.from_service_account_json(GCP_KEYFILE, project=GCP_PROJECT)
    return bigquery.Client(project=GCP_PROJECT)


def load_features(client):
    # create_bqstorage_client=False: the BQ Storage API read path needs
    # bigquery.readsessions.create, which the service account doesn't
    # have (it only has Data Editor + Job User). The plain REST fallback
    # is plenty fast for a table this size.
    df = client.query(f"select * from `{FEATURES_TABLE}`").to_dataframe(
        create_bqstorage_client=False
    )
    df["top_category"] = df["top_category"].fillna("none")
    return df


def build_pipeline():
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        remainder="passthrough",
    )
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=200,
                    max_depth=8,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )


def main():
    client = get_client()
    df = load_features(client)

    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = df["is_churned"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)

    print(f"precision={precision:.4f} recall={recall:.4f} roc_auc={roc_auc:.4f}")

    # Score every customer (not just the held-out test split) for the
    # scores table the dashboard and DAG read from.
    df["churn_score"] = pipeline.predict_proba(X)[:, 1]
    output = df[["user_id", "churn_score", "is_churned"]].rename(
        columns={"is_churned": "is_churned_label"}
    )
    output["scored_at"] = pd.Timestamp.now("UTC")

    client.create_dataset(bigquery.Dataset(f"{GCP_PROJECT}.{GCP_DATASET}"), exists_ok=True)
    job = client.load_table_from_dataframe(
        output,
        SCORES_TABLE,
        job_config=bigquery.LoadJobConfig(write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE),
    )
    job.result()
    print(f"Wrote {len(output)} churn scores to {SCORES_TABLE}")

    return precision, recall, roc_auc


if __name__ == "__main__":
    precision, recall, roc_auc = main()
    if roc_auc < 0.5:
        # Worse than random - something is broken, fail loudly in CI/DAG.
        sys.exit(1)
