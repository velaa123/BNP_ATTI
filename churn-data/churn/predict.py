from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
import pandas as pd


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

ML_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ML_DIR.parent

PROCESSED_DIR = ML_DIR / "data" / "processed"

INPUT_PATH = PROCESSED_DIR / "customer_features.csv"

MODEL_DIR = ML_DIR / "churn" / "model"

OUTPUT_DIR = PROJECT_DIR / "churn-data" / "outputs"

OUTPUT_PATH = OUTPUT_DIR / "churn_predictions.csv"


# ============================================================================
# HELPERS
# ============================================================================

def find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> Optional[str]:
    """
    Find a DataFrame column using case-insensitive matching.
    """

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        key = str(candidate).strip().lower()

        if key in normalized:
            return normalized[key]

    return None


def load_model_package():
    """
    Load the V2 churn model package.

    Expected location:
        ml/churn/model/churn_model.pkl

    Expected package structure:
        {
            "model": trained_model,
            "features": [...],
            "prediction_threshold": ...,
            ...
        }
    """

    candidates = [
        MODEL_DIR / "churn_model.pkl",
        MODEL_DIR / "churn_model.joblib",
    ]

    model_path = None

    for candidate in candidates:
        if candidate.exists():
            model_path = candidate
            break

    if model_path is None:
        raise FileNotFoundError(
            "\nTrained churn model not found.\n"
            f"Expected location:\n{MODEL_DIR}\n\n"
            "Expected file:\n"
            "  churn_model.pkl\n"
        )

    print("\nLoading trained V2 churn model:")
    print(f"  {model_path}")

    if model_path.suffix.lower() == ".joblib":
        package = joblib.load(model_path)
    else:
        with open(model_path, "rb") as file:
            package = pickle.load(file)

    if not isinstance(package, dict):
        raise ValueError(
            "The churn model file does not contain a model package dictionary."
        )

    model = package.get("model")

    if model is None:
        model = package.get("classifier")

    if model is None:
        model = package.get("pipeline")

    if model is None:
        raise ValueError(
            "Model package does not contain 'model', 'classifier', "
            "or 'pipeline'."
        )

    feature_columns = (
        package.get("features")
        or package.get("feature_columns")
    )

    if not feature_columns:
        raise ValueError(
            "Model package does not contain the trained feature list."
        )

    prediction_threshold = (
        package.get("prediction_threshold")
    )

    if prediction_threshold is None:
        prediction_threshold = package.get("threshold")

    if prediction_threshold is None:
        prediction_threshold = 0.50

    prediction_threshold = float(prediction_threshold)

    print(f"  Model features : {len(feature_columns)}")
    print(f"  Threshold      : {prediction_threshold:.2f}")

    return (
        model,
        list(feature_columns),
        prediction_threshold,
        package,
    )


# ============================================================================
# PREPARE MODEL FEATURES
# ============================================================================

def prepare_features(
    df: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """
    Prepare exactly the features used during model training.

    The model was trained using churn_dataset.csv.
    Prediction is performed using customer_features.csv.
    """

    result = pd.DataFrame(index=df.index)

    for feature in feature_columns:

        actual_column = find_column(
            df,
            [feature],
        )

        if actual_column is None:

            raise KeyError(
                f"Required model feature '{feature}' "
                "was not found in customer_features.csv.\n\n"
                "Available columns:\n"
                + "\n".join(
                    f"  - {column}"
                    for column in df.columns
                )
            )

        result[feature] = pd.to_numeric(
            df[actual_column],
            errors="coerce",
        )

    # Replace infinity values.
    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    # Fill missing values using training-compatible median handling.
    for column in result.columns:

        if result[column].isna().any():

            median = result[column].median()

            if pd.isna(median):
                median = 0.0

            result[column] = (
                result[column]
                .fillna(median)
            )

    return result


# ============================================================================
# MODEL PREDICTION
# ============================================================================

def generate_predictions(
    df: pd.DataFrame,
    model,
    feature_columns: list[str],
    prediction_threshold: float,
) -> pd.DataFrame:
    """
    Generate churn probabilities and business-facing prediction fields.
    """

    X = prepare_features(
        df,
        feature_columns,
    )

    # ------------------------------------------------------------------------
    # CHURN PROBABILITY
    # ------------------------------------------------------------------------

    if hasattr(model, "predict_proba"):

        probabilities = (
            model.predict_proba(X)[:, 1]
        )

    else:

        predictions = model.predict(X)

        probabilities = np.asarray(
            predictions,
            dtype=float,
        )

    probabilities = np.clip(
        probabilities,
        0.0,
        1.0,
    )

    result = df.copy()

    result["churn_probability"] = probabilities

    result["churn_prediction"] = (
        result["churn_probability"]
        >= prediction_threshold
    ).astype(int)

    # ------------------------------------------------------------------------
    # RISK SCORE
    # ------------------------------------------------------------------------

    result["risk_score"] = (
        result["churn_probability"] * 100
    ).round(2)

    # ------------------------------------------------------------------------
    # RISK SEGMENT
    # ------------------------------------------------------------------------

    result["risk_segment"] = np.select(
        [
            result["churn_probability"] >= 0.75,
            result["churn_probability"] >= 0.50,
            result["churn_probability"] >= 0.25,
        ],
        [
            "CRITICAL",
            "HIGH",
            "MEDIUM",
        ],
        default="LOW",
    )

    # Backend/segmentation compatibility.
    result["risk_level"] = result["risk_segment"]

    # ------------------------------------------------------------------------
    # DAYS SINCE PURCHASE
    # ------------------------------------------------------------------------

    if "recency_days" in result.columns:

        result["days_since_purchase"] = (
            pd.to_numeric(
                result["recency_days"],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
            .astype(int)
        )

    elif "last_purchase_date" in result.columns:

        last_purchase = pd.to_datetime(
            result["last_purchase_date"],
            errors="coerce",
        )

        reference_date = last_purchase.max()

        result["days_since_purchase"] = (
            reference_date - last_purchase
        ).dt.days.fillna(0).clip(
            lower=0
        ).astype(int)

    else:

        result["days_since_purchase"] = 0

    # ------------------------------------------------------------------------
    # BUSINESS VALUE
    # ------------------------------------------------------------------------

    if "customer_value" in result.columns:

        result["customer_value"] = pd.to_numeric(
            result["customer_value"],
            errors="coerce",
        ).fillna(0).clip(lower=0)

    else:

        result["customer_value"] = 0.0

    if "total_revenue" in result.columns:

        result["total_revenue"] = pd.to_numeric(
            result["total_revenue"],
            errors="coerce",
        ).fillna(0).clip(lower=0)

    else:

        result["total_revenue"] = 0.0

    if "total_orders" in result.columns:

        result["total_orders"] = pd.to_numeric(
            result["total_orders"],
            errors="coerce",
        ).fillna(0)

    else:

        result["total_orders"] = 0

    # Revenue at risk:
    #
    # Expected revenue exposure = historical customer revenue
    # multiplied by predicted churn probability.
    #
    # Example:
    # revenue = 1000
    # churn probability = 0.80
    # revenue at risk = 800

    result["revenue_at_risk"] = (
        result["total_revenue"]
        * result["churn_probability"]
    ).round(2)

    # ------------------------------------------------------------------------
    # EXPLAINABLE REASON
    # ------------------------------------------------------------------------

    reasons = []

    for _, row in result.iterrows():

        candidates = {}

        # Recency risk.
        if "recency_days" in result.columns:

            recency = pd.to_numeric(
                row.get("recency_days", 0),
                errors="coerce",
            )

            if pd.notna(recency):
                candidates["recency"] = float(recency)

        # Frequency risk.
        frequency = row.get(
            "average_purchase_frequency",
            np.nan,
        )

        frequency = pd.to_numeric(
            frequency,
            errors="coerce",
        )

        if pd.notna(frequency):
            candidates["frequency"] = -float(frequency)

        # Cancellation risk.
        cancellation = row.get(
            "cancellation_rate",
            np.nan,
        )

        cancellation = pd.to_numeric(
            cancellation,
            errors="coerce",
        )

        if pd.notna(cancellation):
            candidates["cancellation"] = float(cancellation)

        # Rating risk.
        rating = row.get(
            "average_rating",
            np.nan,
        )

        rating = pd.to_numeric(
            rating,
            errors="coerce",
        )

        if pd.notna(rating):
            candidates["rating"] = -float(rating)

        if not candidates:

            reasons.append(
                "Elevated model-predicted churn risk"
            )
            continue

        strongest = max(
            candidates,
            key=candidates.get,
        )

        if strongest == "recency":
            reasons.append(
                "Long time since last purchase"
            )

        elif strongest == "frequency":
            reasons.append(
                "Low purchase frequency"
            )

        elif strongest == "cancellation":
            reasons.append(
                "High cancellation activity"
            )

        else:
            reasons.append(
                "Low customer rating"
            )

    result["reason"] = reasons

    # ------------------------------------------------------------------------
    # SELECT FINAL OUTPUT
    # ------------------------------------------------------------------------

    output_columns = [
        "customer_id",
        "churn_probability",
        "risk_score",
        "risk_segment",
        "risk_level",
        "churn_prediction",
        "reason",
        "days_since_purchase",
        "customer_value",
        "total_orders",
        "total_revenue",
        "revenue_at_risk",
    ]

    available_columns = [
        column
        for column in output_columns
        if column in result.columns
    ]

    output = result[
        available_columns
    ].copy()

    # Sort highest-risk customers first.
    output = output.sort_values(
        by=[
            "risk_score",
            "revenue_at_risk",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(drop=True)

    return output


# ============================================================================
# MAIN
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Generate V2 ML-based customer churn predictions "
            "for backend integration."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=INPUT_PATH,
        help="Customer feature CSV.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Output churn prediction CSV.",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - V2 ML PREDICTION")
    print("=" * 70)

    # ------------------------------------------------------------------------
    # INPUT
    # ------------------------------------------------------------------------

    print()
    print("[1/5] Loading customer features...")
    print(f"Input file: {args.input}")

    if not args.input.exists():

        raise FileNotFoundError(
            f"\nCustomer feature file not found:\n{args.input}\n\n"
            "Run first:\n"
            "  python preprocessing\\feature_engineering.py"
        )

    df = pd.read_csv(
        args.input
    )

    print("Customer features loaded successfully.")
    print(f"Customers: {len(df)}")
    print(f"Columns : {len(df.columns)}")

    # ------------------------------------------------------------------------
    # MODEL
    # ------------------------------------------------------------------------

    print()
    print("[2/5] Loading trained V2 model...")

    (
        model,
        feature_columns,
        prediction_threshold,
        package,
    ) = load_model_package()

    # ------------------------------------------------------------------------
    # PREDICTION
    # ------------------------------------------------------------------------

    print()
    print("[3/5] Generating ML churn predictions...")

    predictions = generate_predictions(
        df,
        model,
        feature_columns,
        prediction_threshold,
    )

    print("Predictions generated successfully.")

    # ------------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------------

    print()
    print("[4/5] Calculating business summary...")

    total_customers = len(predictions)

    churned = (
        predictions["churn_prediction"] == 1
    ).sum()

    active = (
        predictions["churn_prediction"] == 0
    ).sum()

    total_revenue_at_risk = (
        predictions["revenue_at_risk"]
        .sum()
    )

    critical_revenue = (
        predictions.loc[
            predictions["risk_segment"] == "CRITICAL",
            "revenue_at_risk",
        ]
        .sum()
    )

    high_critical_revenue = (
        predictions.loc[
            predictions["risk_segment"].isin(
                [
                    "CRITICAL",
                    "HIGH",
                ]
            ),
            "revenue_at_risk",
        ]
        .sum()
    )

    print()
    print("Prediction distribution:")
    print(
        f"  Model-predicted active : "
        f"{active} ({active / total_customers * 100:.2f}%)"
    )
    print(
        f"  Model-predicted churned: "
        f"{churned} ({churned / total_customers * 100:.2f}%)"
    )

    print()
    print("Risk segment distribution:")

    for segment in [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ]:

        count = (
            predictions["risk_segment"]
            == segment
        ).sum()

        percentage = (
            count / total_customers * 100
            if total_customers > 0
            else 0
        )

        print(
            f"  {segment:<10}: "
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print("Revenue at risk:")
    print(
        f"  Total        : "
        f"{total_revenue_at_risk:,.2f}"
    )
    print(
        f"  Critical     : "
        f"{critical_revenue:,.2f}"
    )
    print(
        f"  High+Critical: "
        f"{high_critical_revenue:,.2f}"
    )

    # ------------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------------

    print()
    print("[5/5] Saving churn predictions...")

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    predictions.to_csv(
        args.output,
        index=False,
    )

    print("Churn predictions saved successfully.")
    print(f"Output file: {args.output}")

    # ------------------------------------------------------------------------
    # PREVIEW
    # ------------------------------------------------------------------------

    print()
    print("Output columns:")
    print(
        "  "
        + ", ".join(predictions.columns)
    )

    print()
    print("Top 10 highest-risk customers:")

    preview_columns = [
        "customer_id",
        "risk_score",
        "risk_segment",
        "reason",
        "days_since_purchase",
        "customer_value",
        "total_orders",
        "revenue_at_risk",
    ]

    available_preview = [
        column
        for column in preview_columns
        if column in predictions.columns
    ]

    print(
        predictions[
            available_preview
        ]
        .head(10)
        .to_string(index=False)
    )

    print()
    print("=" * 70)
    print("V2 ML CHURN PREDICTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()