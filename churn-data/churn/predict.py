"""
predict.py

Customer churn prediction and active-customer ranking.

This module supports:

1. Existing model-based churn prediction.
2. Backend handoff ranking using an explainable risk score.

Active customer ranking formula:

    risk_score =
        100 * (
            0.55 * recency_component
            + 0.25 * frequency_component
            + 0.20 * rating_component
        )

Higher score = higher churn/outreach risk.

Risk segments:

    HIGH   : score >= 70
    MEDIUM : score >= 40
    LOW    : score < 40
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np
import pandas as pd


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"

RAW_DATA_PATH = DATA_DIR / "raw" / "dataset.xls"

PROCESSED_DATA_PATH = (
    DATA_DIR / "processed" / "cleaned_data.csv"
)

MODEL_DIR = BASE_DIR / "models"

OUTPUT_DIR = BASE_DIR / "outputs"


# ============================================================================
# MODEL FEATURE CONFIGURATION
# ============================================================================

DEFAULT_FEATURE_COLUMNS = [
    "age",
    "cancellations_count",
    "unit_price",
    "quantity",
    "purchase_frequency",
    "Ratings",
]


# ============================================================================
# GENERAL HELPERS
# ============================================================================

def _find_column(
    df: pd.DataFrame,
    candidates: list[str],
) -> Optional[str]:
    """
    Find a DataFrame column using case-insensitive matching.

    Example:
        Ratings
        rating
        RATING

    are treated as equivalent.
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


def _percentile(values: pd.Series) -> pd.Series:
    """
    Convert values into percentile ranks from 0 to 1.
    """

    numeric = pd.to_numeric(
        values,
        errors="coerce"
    )

    if numeric.empty:
        return pd.Series(
            0.0,
            index=values.index
        )

    if numeric.nunique(dropna=True) <= 1:

        return pd.Series(
            0.5,
            index=values.index
        )

    return (
        numeric.rank(
            method="average",
            pct=True
        )
        .fillna(0.5)
    )


def _normalise_status(value) -> str:
    """
    Normalize subscription status.
    """

    if pd.isna(value):
        return ""

    return (
        str(value)
        .strip()
        .lower()
    )


# ============================================================================
# ACTIVE CUSTOMER RANKING
# ============================================================================

def rank_active_customers(
    customers: pd.DataFrame,
    as_of: Optional[str] = None,
) -> Tuple[pd.DataFrame, pd.Timestamp]:
    """
    Rank active customers using an explainable churn/outreach score.

    Required logical fields:

        customer_id
        subscription_status
        last_purchase_date
        purchase_frequency
        Ratings

    The actual DataFrame column names are detected
    case-insensitively.

    Returns:

        ranked DataFrame
        cutoff date
    """

    if not isinstance(customers, pd.DataFrame):
        raise TypeError(
            "customers must be a pandas DataFrame."
        )

    df = customers.copy()

    # ------------------------------------------------------------------------
    # FIND REQUIRED COLUMNS
    # ------------------------------------------------------------------------

    customer_id_col = _find_column(
        df,
        [
            "customer_id",
            "customer id",
            "customerid",
        ],
    )

    status_col = _find_column(
        df,
        [
            "subscription_status",
            "subscription status",
            "status",
        ],
    )

    purchase_date_col = _find_column(
        df,
        [
            "last_purchase_date",
            "last purchase date",
            "last_purchase",
            "purchase_date",
        ],
    )

    frequency_col = _find_column(
        df,
        [
            "purchase_frequency",
            "purchase frequency",
            "average_purchase_frequency",
            "avg_purchase_frequency",
            "purchase_freq",
            "frequency",
        ],
    )

    # IMPORTANT:
    # The dataset uses "Ratings".
    # This list deliberately includes Ratings.
    rating_col = _find_column(
        df,
        [
            "Ratings",
            "rating",
            "ratings",
            "average_rating",
            "customer_rating",
            "satisfaction_rating",
        ],
    )

    missing = []

    if customer_id_col is None:
        missing.append("customer_id")

    if status_col is None:
        missing.append("subscription_status")

    if purchase_date_col is None:
        missing.append("last_purchase_date")

    if frequency_col is None:
        missing.append("purchase_frequency")

    if rating_col is None:
        missing.append("Ratings")

    if missing:

        available = "\n".join(
            f"  - {column}"
            for column in df.columns
        )

        raise KeyError(
            "Required ranking columns are missing:\n"
            + "\n".join(
                f"  - {column}"
                for column in missing
            )
            + "\n\nAvailable columns:\n"
            + available
        )

    # ------------------------------------------------------------------------
    # PREPARE DATA
    # ------------------------------------------------------------------------

    df["_customer_id"] = df[customer_id_col].astype(str).str.strip()

    df["_status"] = (
        df[status_col]
        .map(_normalise_status)
    )

    df["_purchase_date"] = pd.to_datetime(
        df[purchase_date_col],
        errors="coerce"
    )

    df["_purchase_frequency"] = pd.to_numeric(
        df[frequency_col],
        errors="coerce"
    )

    df["_rating"] = pd.to_numeric(
        df[rating_col],
        errors="coerce"
    )

    # ------------------------------------------------------------------------
    # ACTIVE CUSTOMER FILTER
    # ------------------------------------------------------------------------

    active_statuses = {
        "active",
        "subscribed",
        "current",
    }

    active_mask = (
        df["_status"]
        .isin(active_statuses)
    )

    df = df.loc[active_mask].copy()

    if df.empty:

        raise ValueError(
            "No active customers were found.\n"
            "Expected subscription_status values such as "
            "'active', 'subscribed', or 'current'."
        )

    # ------------------------------------------------------------------------
    # VALID DATA FILTER
    # ------------------------------------------------------------------------

    df = df[
        df["_purchase_date"].notna()
    ].copy()

    df = df[
        df["_purchase_frequency"].notna()
    ].copy()

    df = df[
        df["_purchase_frequency"] >= 0
    ].copy()

    df = df[
        df["_rating"].notna()
    ].copy()

    df = df[
        (df["_rating"] >= 0)
        & (df["_rating"] <= 5)
    ].copy()

    if df.empty:

        raise ValueError(
            "No valid active customer records remain after "
            "date, purchase-frequency, and rating validation."
        )

    # ------------------------------------------------------------------------
    # DETERMINE AS-OF DATE
    # ------------------------------------------------------------------------

    if as_of:

        cutoff = pd.to_datetime(
            as_of,
            errors="coerce"
        )

        if pd.isna(cutoff):

            raise ValueError(
                "Invalid --as-of date. "
                "Use YYYY-MM-DD."
            )

        cutoff = pd.Timestamp(cutoff)

    else:

        cutoff = pd.Timestamp(
            df["_purchase_date"].max()
        )

    # ------------------------------------------------------------------------
    # REMOVE FUTURE PURCHASE DATES
    # ------------------------------------------------------------------------

    df = df[
        df["_purchase_date"] <= cutoff
    ].copy()

    if df.empty:

        raise ValueError(
            "No active customer records remain after "
            "applying the snapshot date."
        )

    # ------------------------------------------------------------------------
    # RECENCY
    # ------------------------------------------------------------------------

    df["days_since_purchase"] = (
        cutoff - df["_purchase_date"]
    ).dt.days

    # Protect against negative values.
    df["days_since_purchase"] = (
        df["days_since_purchase"]
        .clip(lower=0)
    )

    # Higher recency = higher risk.
    recency_component = _percentile(
        df["days_since_purchase"]
    )

    # ------------------------------------------------------------------------
    # PURCHASE FREQUENCY
    # ------------------------------------------------------------------------

    # Lower purchase frequency = higher risk.
    frequency_percentile = _percentile(
        df["_purchase_frequency"]
    )

    frequency_component = (
        1.0 - frequency_percentile
    )

    # ------------------------------------------------------------------------
    # CUSTOMER RATING
    # ------------------------------------------------------------------------

    # Lower rating = higher risk.
    rating_percentile = _percentile(
        df["_rating"]
    )

    rating_component = (
        1.0 - rating_percentile
    )

    # ------------------------------------------------------------------------
    # FINAL RISK SCORE
    # ------------------------------------------------------------------------

    df["risk_score"] = (
        100.0
        * (
            0.55 * recency_component
            + 0.25 * frequency_component
            + 0.20 * rating_component
        )
    )

    df["risk_score"] = (
        df["risk_score"]
        .clip(0, 100)
        .round(2)
    )

    # ------------------------------------------------------------------------
    # RISK SEGMENT
    # ------------------------------------------------------------------------

    df["risk_segment"] = np.select(
        [
            df["risk_score"] >= 70,
            df["risk_score"] >= 40,
        ],
        [
            "High",
            "Medium",
        ],
        default="Low",
    )

    # ------------------------------------------------------------------------
    # EXPLAINABLE REASON
    # ------------------------------------------------------------------------

    component_values = pd.DataFrame(
        {
            "recency": recency_component,
            "frequency": frequency_component,
            "rating": rating_component,
        },
        index=df.index,
    )

    strongest_component = (
        component_values.idxmax(axis=1)
    )

    def make_reason(component: str) -> str:

        if component == "recency":
            return (
                "Long time since last purchase"
            )

        if component == "frequency":
            return (
                "Low purchase frequency"
            )

        return (
            "Low customer rating"
        )

    df["reason"] = (
        strongest_component
        .map(make_reason)
    )

    # ------------------------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------------------------

    ranked = df[
        [
            "_customer_id",
            "risk_score",
            "risk_segment",
            "reason",
            "days_since_purchase",
        ]
    ].copy()

    ranked = ranked.rename(
        columns={
            "_customer_id": "customer_id"
        }
    )

    ranked = ranked.sort_values(
        by=[
            "risk_score",
            "days_since_purchase",
        ],
        ascending=[
            False,
            False,
        ],
    ).reset_index(drop=True)

    return ranked, cutoff


# ============================================================================
# MODEL LOADING
# ============================================================================

def _find_model_file() -> Optional[Path]:
    """
    Find a trained model file if available.
    """

    if not MODEL_DIR.exists():
        return None

    candidates = [
        MODEL_DIR / "churn_model.pkl",
        MODEL_DIR / "churn_model.joblib",
        MODEL_DIR / "model.pkl",
        MODEL_DIR / "model.joblib",
        MODEL_DIR / "churn_model_package.pkl",
        MODEL_DIR / "churn_model_package.joblib",
    ]

    for path in candidates:

        if path.exists():
            return path

    discovered = list(
        MODEL_DIR.glob("*.pkl")
    )

    if discovered:
        return discovered[0]

    discovered = list(
        MODEL_DIR.glob("*.joblib")
    )

    if discovered:
        return discovered[0]

    return None


def load_model():
    """
    Load a trained churn model.

    Returns:

        model
        feature_columns
        prediction_threshold
        model_package
    """

    model_path = _find_model_file()

    if model_path is None:

        raise FileNotFoundError(
            "No trained model file was found in:\n"
            f"{MODEL_DIR}\n\n"
            "Expected a .pkl or .joblib model file."
        )

    print(
        f"Loading trained model:\n"
        f"  {model_path}"
    )

    if model_path.suffix.lower() == ".joblib":

        package = joblib.load(
            model_path
        )

    else:

        with open(
            model_path,
            "rb"
        ) as file:

            package = pickle.load(file)

    # --------------------------------------------------------
    # Handle packaged models
    # --------------------------------------------------------

    if isinstance(package, dict):

        model = (
            package.get("model")
            or package.get("classifier")
            or package.get("pipeline")
        )

        if model is None:

            raise ValueError(
                "Model package does not contain "
                "'model', 'classifier', or 'pipeline'."
            )

        feature_columns = (
            package.get("feature_columns")
            or package.get("features")
            or DEFAULT_FEATURE_COLUMNS
        )

        prediction_threshold = (
            package.get("prediction_threshold")
            or package.get("threshold")
            or 0.50
        )

        return (
            model,
            list(feature_columns),
            float(prediction_threshold),
            package,
        )

    # --------------------------------------------------------
    # Handle direct model
    # --------------------------------------------------------

    model = package

    feature_columns = getattr(
        model,
        "feature_names_in_",
        DEFAULT_FEATURE_COLUMNS,
    )

    return (
        model,
        list(feature_columns),
        0.50,
        {
            "model": model
        },
    )


# ============================================================================
# MODEL FEATURE PREPARATION
# ============================================================================

def prepare_features(
    df: pd.DataFrame,
    feature_columns,
) -> pd.DataFrame:
    """
    Prepare model features.

    Handles the dataset's Ratings column correctly.
    """

    result = pd.DataFrame(
        index=df.index
    )

    for feature in feature_columns:

        actual_column = _find_column(
            df,
            [feature]
        )

        if actual_column is None:

            # Try common aliases.
            if str(feature).lower() == "rating":

                actual_column = _find_column(
                    df,
                    [
                        "Ratings",
                        "rating",
                        "ratings",
                    ],
                )

        if actual_column is None:

            raise KeyError(
                f"Model feature '{feature}' "
                "was not found in the dataset.\n\n"
                "Available columns:\n"
                + "\n".join(
                    f"  - {column}"
                    for column in df.columns
                )
            )

        result[feature] = pd.to_numeric(
            df[actual_column],
            errors="coerce"
        )

    # Fill numeric missing values using median.
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

def predict_churn(
    df: pd.DataFrame,
):
    """
    Generate model-based churn probabilities.
    """

    (
        model,
        feature_columns,
        prediction_threshold,
        model_package,
    ) = load_model()

    X = prepare_features(
        df,
        feature_columns
    )

    if hasattr(
        model,
        "predict_proba"
    ):

        probabilities = (
            model
            .predict_proba(X)[:, 1]
        )

    else:

        predictions = model.predict(X)

        probabilities = np.asarray(
            predictions,
            dtype=float
        )

    result = df.copy()

    result["churn_probability"] = (
        probabilities
    )

    result["churn_prediction"] = (
        result["churn_probability"]
        >= prediction_threshold
    ).astype(int)

    return (
        result,
        prediction_threshold,
        model_package,
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Customer churn prediction "
            "and active customer ranking."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=RAW_DATA_PATH,
        help="Input Excel dataset.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DIR,
        help="Output directory.",
    )

    parser.add_argument(
        "--as-of",
        default=None,
        help="Optional snapshot date in YYYY-MM-DD format.",
    )

    parser.add_argument(
        "--mode",
        choices=[
            "ranking",
            "model",
        ],
        default="ranking",
        help="Prediction mode.",
    )

    args = parser.parse_args()

    # ------------------------------------------------------------------------
    # INPUT VALIDATION
    # ------------------------------------------------------------------------

    if not args.input.exists():

        raise FileNotFoundError(
            "Input dataset not found:\n"
            f"{args.input}"
        )

    args.output.mkdir(
        parents=True,
        exist_ok=True
    )

    # ------------------------------------------------------------------------
    # LOAD DATA
    # ------------------------------------------------------------------------

    print()
    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - PREDICTION")
    print("=" * 70)

    print()
    print("Input file:")
    print(f"  {args.input}")

    df = pd.read_excel(
        args.input
    )

    print()
    print(
        f"Dataset loaded: "
        f"{len(df)} rows"
    )

    # ------------------------------------------------------------------------
    # RANKING MODE
    # ------------------------------------------------------------------------

    if args.mode == "ranking":

        ranked, cutoff = rank_active_customers(
            df,
            as_of=args.as_of,
        )

        # Save full ranking.
        predictions_path = (
            args.output
            / "churn_predictions.csv"
        )

        ranked.to_csv(
            predictions_path,
            index=False
        )

        # Save compact segment file.
        segments_path = (
            args.output
            / "customer_segments.csv"
        )

        ranked[
            [
                "customer_id",
                "risk_score",
                "risk_segment",
            ]
        ].to_csv(
            segments_path,
            index=False
        )

        # Print summary.
        print()
        print("=" * 70)
        print("CUSTOMER RANKING COMPLETE")
        print("=" * 70)

        print()
        print(
            f"Snapshot date : "
            f"{cutoff.strftime('%Y-%m-%d')}"
        )

        print(
            f"Active customers ranked : "
            f"{len(ranked)}"
        )

        print()
        print("Risk distribution:")

        print(
            ranked[
                "risk_segment"
            ]
            .value_counts()
            .to_string()
        )

        print()
        print("Output files:")

        print(
            f"  {predictions_path}"
        )

        print(
            f"  {segments_path}"
        )

        print()
        print("Top 10 active customers:")

        print(
            ranked
            .head(10)
            .to_string(index=False)
        )

        return

    # ------------------------------------------------------------------------
    # MODEL MODE
    # ------------------------------------------------------------------------

    predicted, threshold, package = (
        predict_churn(df)
    )

    model_output_path = (
        args.output
        / "model_churn_predictions.csv"
    )

    predicted.to_csv(
        model_output_path,
        index=False
    )

    print()
    print("=" * 70)
    print("MODEL PREDICTION COMPLETE")
    print("=" * 70)

    print()
    print(
        f"Prediction threshold: "
        f"{threshold:.2f}"
    )

    print(
        f"Rows predicted: "
        f"{len(predicted)}"
    )

    print()
    print(
        f"Output file:\n"
        f"  {model_output_path}"
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()