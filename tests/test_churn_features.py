import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ml"))
from train import NUMERIC_FEATURES, build_pipeline


def test_recency_days_excluded_from_features():
    """is_churned is partly *defined* as recency_days > 90 in dbt, so
    including it as a feature would let the model trivially learn the
    label definition instead of a real pattern. Guards against that
    regression creeping back in."""
    assert "recency_days" not in NUMERIC_FEATURES


def test_pipeline_fits_and_predicts_on_synthetic_data():
    df = pd.DataFrame(
        {
            "frequency": [0, 1, 5, 10, 0, 2],
            "monetary": [0.0, 50.0, 300.0, 900.0, 0.0, 80.0],
            "distinct_categories": [0, 1, 3, 4, 0, 2],
            "top_category": ["none", "Jeans", "Shoes", "Jeans", "none", "Shoes"],
        }
    )
    y = pd.Series([1, 1, 0, 0, 1, 0])

    pipeline = build_pipeline()
    pipeline.fit(df, y)
    preds = pipeline.predict(df)

    assert len(preds) == len(df)
    assert set(preds).issubset({0, 1})


def test_pipeline_handles_unseen_category_at_predict_time():
    train_df = pd.DataFrame(
        {
            "frequency": [1, 5],
            "monetary": [50.0, 300.0],
            "distinct_categories": [1, 3],
            "top_category": ["Jeans", "Shoes"],
        }
    )
    y = pd.Series([1, 0])

    pipeline = build_pipeline()
    pipeline.fit(train_df, y)

    unseen_df = pd.DataFrame(
        {
            "frequency": [2],
            "monetary": [75.0],
            "distinct_categories": [1],
            "top_category": ["Outerwear & Coats"],
        }
    )
    preds = pipeline.predict(unseen_df)

    assert len(preds) == 1
