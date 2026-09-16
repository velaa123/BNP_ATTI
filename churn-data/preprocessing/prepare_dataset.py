"""
Customer Churn Project - Dataset Preparation V2

Purpose:
    Prepare the customer-level feature dataset for churn model training.

Target:
    Since the source dataset does not contain an explicit churn column,
    churn is created using customer inactivity.

    Customers in the highest 25% of recency_days are treated as churned.

Important:
    recency_days is used to construct the target and is therefore removed
    from the model feature set.

Output:
    ml/data/processed/churn_dataset.csv
"""

from pathlib import Path
import sys

import numpy as np
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "customer_features.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "churn_dataset.csv"
)


# ============================================================
# REQUIRED FEATURES
# ============================================================

REQUIRED_FEATURES = [
    "customer_id",
    "age",
    "gender",
    "country",
    "subscription_status",

    "total_orders",
    "total_quantity",
    "total_revenue",
    "average_order_value",
    "average_unit_price",
    "average_rating",
    "total_cancellations",

    "average_purchase_frequency",
    "max_purchase_frequency",
    "min_purchase_frequency",

    "first_purchase_date",
    "last_purchase_date",
    "signup_date",

    "recency_days",
    "tenure_days",
    "orders_per_month",
    "average_quantity_per_order",

    "product_diversity",
    "category_diversity",
    "product_name_diversity",

    "cancellation_rate",
    "revenue_per_order",
    "revenue_per_unit",

    "purchase_activity_ratio",
    "customer_value",

    # V2 features
    "revenue_per_month",
    "quantity_per_month",
    "cancellation_per_order",
    "rating_adjusted_value",
    "frequency_consistency",
    "purchase_intensity",
    "revenue_intensity",
    "quantity_intensity",
    "customer_value_per_month",
    "tenure_years",
    "orders_per_tenure_year",
    "revenue_per_order_month",
    "revenue_x_frequency",
    "orders_x_purchase_activity",
    "value_x_purchase_activity",
    "cancellation_x_frequency",
    "diversity_ratio",

    "recency_band",
    "value_band",
    "frequency_band",
]


# ============================================================
# MODEL FEATURES
# ============================================================

MODEL_FEATURES = [
    "age",

    "total_orders",
    "total_quantity",
    "total_revenue",

    "average_order_value",
    "average_unit_price",
    "average_rating",

    "total_cancellations",

    "average_purchase_frequency",
    "max_purchase_frequency",
    "min_purchase_frequency",

    "tenure_days",
    "orders_per_month",
    "average_quantity_per_order",

    "product_diversity",
    "category_diversity",
    "product_name_diversity",

    "cancellation_rate",

    "revenue_per_order",
    "revenue_per_unit",

    "purchase_activity_ratio",
    "customer_value",

    # ========================================================
    # FEATURE ENGINEERING V2
    # ========================================================

    "revenue_per_month",
    "quantity_per_month",
    "cancellation_per_order",
    "rating_adjusted_value",
    "frequency_consistency",

    "purchase_intensity",
    "revenue_intensity",
    "quantity_intensity",

    "customer_value_per_month",
    "tenure_years",
    "orders_per_tenure_year",
    "revenue_per_order_month",

    "revenue_x_frequency",
    "orders_x_purchase_activity",
    "value_x_purchase_activity",
    "cancellation_x_frequency",

    "diversity_ratio",
]


# ============================================================
# DISPLAY
# ============================================================

def print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# VALIDATE FEATURES
# ============================================================

def validate_required_features(
    df: pd.DataFrame
) -> None:

    missing_columns = [
        column
        for column in REQUIRED_FEATURES
        if column not in df.columns
    ]

    if missing_columns:

        print("\nERROR: Missing required columns:")

        for column in missing_columns:
            print(f"  - {column}")

        sys.exit(1)


# ============================================================
# NUMERIC PREPARATION
# ============================================================

def prepare_numeric_features(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    for column in MODEL_FEATURES:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    df[MODEL_FEATURES] = df[
        MODEL_FEATURES
    ].replace(
        [np.inf, -np.inf],
        np.nan
    )

    for column in MODEL_FEATURES:

        if df[column].isna().any():

            median_value = df[column].median()

            if pd.isna(median_value):
                median_value = 0.0

            df[column] = (
                df[column]
                .fillna(median_value)
            )

    return df


# ============================================================
# CREATE CHURN TARGET
# ============================================================

def create_churn_target(
    df: pd.DataFrame
) -> tuple[pd.DataFrame, float]:

    df = df.copy()

    if "recency_days" not in df.columns:

        print(
            "\nERROR: recency_days column is missing."
        )

        sys.exit(1)

    recency = pd.to_numeric(
        df["recency_days"],
        errors="coerce"
    )

    if recency.isna().all():

        print(
            "\nERROR: recency_days contains "
            "no usable numeric values."
        )

        sys.exit(1)

    recency_median = recency.median()

    if pd.isna(recency_median):
        recency_median = 0.0

    recency = recency.fillna(
        recency_median
    )

    # --------------------------------------------------------
    # Data-driven threshold
    # --------------------------------------------------------

    churn_threshold = float(
        recency.quantile(0.75)
    )

    df["churn"] = (
        recency >= churn_threshold
    ).astype(int)

    # --------------------------------------------------------
    # Handle extreme ties
    # --------------------------------------------------------

    churn_rate = df["churn"].mean()

    if (
        churn_rate > 0.40
        or churn_rate < 0.10
    ):

        recency_rank_percentile = (
            recency.rank(
                method="first",
                pct=True
            )
        )

        df["churn"] = (
            recency_rank_percentile >= 0.75
        ).astype(int)

    return df, churn_threshold


# ============================================================
# REMOVE LEAKAGE
# ============================================================

def remove_target_leakage(
    df: pd.DataFrame
) -> pd.DataFrame:

    df = df.copy()

    leakage_columns = []

    for column in [
        "recency_days",
        "churn_label"
    ]:

        if column in df.columns:

            leakage_columns.append(
                column
            )

    if leakage_columns:

        df = df.drop(
            columns=leakage_columns,
            errors="ignore"
        )

    print(
        "Removed leakage columns:",
        (
            leakage_columns
            if leakage_columns
            else "None"
        )
    )

    return df


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

def print_target_distribution(
    df: pd.DataFrame
) -> None:

    total = len(df)

    active_count = int(
        (df["churn"] == 0).sum()
    )

    churned_count = int(
        (df["churn"] == 1).sum()
    )

    active_percentage = (
        active_count / total * 100
        if total > 0
        else 0
    )

    churned_percentage = (
        churned_count / total * 100
        if total > 0
        else 0
    )

    print("\nChurn distribution:")

    print(
        f"  Active customers : "
        f"{active_count} "
        f"({active_percentage:.2f}%)"
    )

    print(
        f"  Churned customers: "
        f"{churned_count} "
        f"({churned_percentage:.2f}%)"
    )

    print(
        f"  Total customers  : "
        f"{total}"
    )

    print(
        f"  Churn rate       : "
        f"{churned_percentage:.2f}%"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print_header(
        "CUSTOMER CHURN PROJECT - DATASET PREPARATION V2"
    )

    # ========================================================
    # 1. LOAD
    # ========================================================

    print(
        "\n[1/6] Loading customer features..."
    )

    print(
        f"Input file: {INPUT_FILE}"
    )

    if not INPUT_FILE.exists():

        print(
            "\nERROR: Input file does not exist."
        )

        print(
            f"Expected file: {INPUT_FILE}"
        )

        sys.exit(1)

    try:

        df = pd.read_csv(
            INPUT_FILE
        )

    except Exception as error:

        print(
            "\nERROR: Failed to load input file."
        )

        print(
            f"Details: {error}"
        )

        sys.exit(1)

    print(
        "Customer features loaded successfully."
    )

    print(
        f"Rows: {len(df)}"
    )

    print(
        f"Columns: {len(df.columns)}"
    )

    # ========================================================
    # 2. VALIDATE
    # ========================================================

    print(
        "\n[2/6] Validating required features..."
    )

    validate_required_features(df)

    print(
        "All required V2 features are available."
    )

    # ========================================================
    # 3. NUMERIC
    # ========================================================

    print(
        "\n[3/6] Preparing numeric features..."
    )

    df = prepare_numeric_features(
        df
    )

    print(
        f"Model features available: "
        f"{len(MODEL_FEATURES)}"
    )

    # ========================================================
    # 4. TARGET
    # ========================================================

    print(
        "\n[4/6] Creating churn target..."
    )

    df, churn_threshold = (
        create_churn_target(df)
    )

    print(
        f"Churn threshold: "
        f"{churn_threshold:.2f} days"
    )

    print(
        "Target definition: customers at or "
        "above the 75th percentile of inactivity "
        "are labeled as churned."
    )

    print_target_distribution(
        df
    )

    # ========================================================
    # 5. REMOVE LEAKAGE
    # ========================================================

    print(
        "\n[5/6] Removing target leakage features..."
    )

    df = remove_target_leakage(
        df
    )

    # --------------------------------------------------------
    # Final column ordering
    # --------------------------------------------------------

    preferred_columns = [
        "customer_id",
        "churn"
    ]

    remaining_columns = [
        column
        for column in df.columns
        if column not in preferred_columns
    ]

    df = df[
        preferred_columns
        + remaining_columns
    ]

    if "customer_id" in df.columns:

        df = (
            df.sort_values(
                by="customer_id"
            )
            .reset_index(drop=True)
        )

    print(
        "\nFinal model features:"
    )

    for feature in MODEL_FEATURES:

        if feature in df.columns:
            print(
                f"  - {feature}"
            )

    # ========================================================
    # 6. SAVE
    # ========================================================

    print(
        "\n[6/6] Saving prepared churn dataset..."
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    try:

        df.to_csv(
            OUTPUT_FILE,
            index=False
        )

    except Exception as error:

        print(
            "\nERROR: Failed to save output dataset."
        )

        print(
            f"Details: {error}"
        )

        sys.exit(1)

    print(
        "Prepared churn dataset saved successfully."
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    # ========================================================
    # FINAL
    # ========================================================

    print("\n")

    print_header(
        "DATASET PREPARATION V2 COMPLETE"
    )

    print(
        f"Customers: {len(df)}"
    )

    print(
        f"Columns  : {len(df.columns)}"
    )

    print(
        f"Model features: {len(MODEL_FEATURES)}"
    )

    print(
        "\nTarget distribution:"
    )

    active_count = int(
        (df["churn"] == 0).sum()
    )

    churned_count = int(
        (df["churn"] == 1).sum()
    )

    total = len(df)

    print(
        f"  0 (Active): "
        f"{active_count} customers "
        f"({active_count / total * 100:.2f}%)"
    )

    print(
        f"  1 (Churned): "
        f"{churned_count} customers "
        f"({churned_count / total * 100:.2f}%)"
    )

    print(
        "\nFinal dataset shape:"
    )

    print(
        df.shape
    )

    print("\n")

    print("=" * 70)
    print("NEXT STEP:")
    print("Train and benchmark all four models.")
    print("Then run threshold_analysis.py.")
    print("=" * 70)


if __name__ == "__main__":
    main()