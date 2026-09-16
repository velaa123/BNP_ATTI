from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from preprocessing.clean_data import load_customers
from preprocessing.feature_engineering import add_risk_features


def train_clusters():
    ml_folder = Path(__file__).resolve().parents[1]
    customers = load_customers(ml_folder / "data/raw/dataset.xls")

    as_of = customers["last_purchase_date"].max()
    active = add_risk_features(customers, as_of)

    columns = ["days_since_purchase", "purchase_frequency", "Ratings"]
    x = active[columns]

    model = make_pipeline(
        StandardScaler(),
        KMeans(n_clusters=3, n_init=10, random_state=42),
    )

    active["cluster_id"] = model.fit_predict(x)

    model_folder = ml_folder / "churn/model"
    output_folder = ml_folder / "outputs"
    model_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)

    joblib.dump(model, model_folder / "behavior_clusters.joblib")

    active[["customer_id", "cluster_id", *columns]].to_csv(
        output_folder / "behavior_segments.csv", index=False
    )

    print("Customers grouped:", len(active))
    print(active["cluster_id"].value_counts().sort_index())
    print(
    active.groupby("cluster_id")[
        ["days_since_purchase", "purchase_frequency", "Ratings"]
    ].mean().round(1)
)


if __name__ == "__main__":
    train_clusters()