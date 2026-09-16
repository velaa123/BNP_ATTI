"""
Customer Churn Project - Feature Engineering V2

Purpose:
    Create customer-level behavioral features for churn prediction.

Version:
    Feature Engineering V2

Important:
    recency_days is created because it is required for the behavioral
    churn target, but it is removed later by prepare_dataset.py before
    model training.

Input:
    ml/data/processed/cleaned_data.csv

Output:
    ml/data/processed/customer_features.csv
"""

import os
import pandas as pd
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

INPUT_FILE = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "processed",
    "cleaned_data.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "data",
    "processed"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "customer_features.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - FEATURE ENGINEERING V2")
    print("=" * 70)

    print("\n[1/8] Loading cleaned dataset...")
    print(f"Input file: {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"\nCleaned dataset not found.\n"
            f"Expected location:\n{INPUT_FILE}\n\n"
            f"Run clean_data.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# PREPARE DATA TYPES
# ============================================================

def prepare_data(df):
    print("\n[2/8] Preparing data types...")

    df = df.copy()

    df["signup_date"] = pd.to_datetime(
        df["signup_date"],
        errors="coerce"
    )

    df["last_purchase_date"] = pd.to_datetime(
        df["last_purchase_date"],
        errors="coerce"
    )

    numeric_columns = [
        "age",
        "cancellations_count",
        "unit_price",
        "quantity",
        "purchase_frequency",
        "Ratings"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    print("Data types prepared.")

    return df


# ============================================================
# ORDER-LEVEL FEATURES
# ============================================================

def create_order_features(df):
    print("\n[3/8] Creating order-level features...")

    df = df.copy()

    # Total value of the order.
    df["order_value"] = (
        df["unit_price"] * df["quantity"]
    )

    # Customer lifetime represented by this transaction.
    df["customer_tenure_days"] = (
        df["last_purchase_date"]
        - df["signup_date"]
    ).dt.days

    df["customer_tenure_days"] = (
        df["customer_tenure_days"]
        .clip(lower=0)
    )

    # Unit price is already the effective price per unit.
    df["price_per_unit"] = df["unit_price"]

    print("Order-level features created:")
    print("  - order_value")
    print("  - customer_tenure_days")
    print("  - price_per_unit")

    return df


# ============================================================
# CUSTOMER-LEVEL FEATURES
# ============================================================

def create_customer_features(df):
    print("\n[4/8] Creating customer-level behavioral features...")

    df = df.copy()

    # --------------------------------------------------------
    # Reference date
    # --------------------------------------------------------

    reference_date = df["last_purchase_date"].max()

    if pd.isna(reference_date):
        raise ValueError(
            "Could not determine reference date because "
            "last_purchase_date contains no valid dates."
        )

    print(f"Reference date: {reference_date.date()}")

    # --------------------------------------------------------
    # Base customer aggregation
    # --------------------------------------------------------

    customer_features = (
        df.groupby("customer_id")
        .agg(
            total_orders=("order_id", "nunique"),
            total_quantity=("quantity", "sum"),
            total_revenue=("order_value", "sum"),
            average_order_value=("order_value", "mean"),
            average_unit_price=("unit_price", "mean"),
            average_rating=("Ratings", "mean"),
            total_cancellations=("cancellations_count", "sum"),

            average_purchase_frequency=(
                "purchase_frequency",
                "mean"
            ),

            max_purchase_frequency=(
                "purchase_frequency",
                "max"
            ),

            min_purchase_frequency=(
                "purchase_frequency",
                "min"
            ),

            first_purchase_date=(
                "last_purchase_date",
                "min"
            ),

            last_purchase_date=(
                "last_purchase_date",
                "max"
            ),

            signup_date=(
                "signup_date",
                "min"
            ),

            age=("age", "first"),
            gender=("gender", "first"),
            country=("country", "first"),

            subscription_status=(
                "subscription_status",
                "first"
            )
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # Recency
    # --------------------------------------------------------

    customer_features["recency_days"] = (
        reference_date
        - customer_features["last_purchase_date"]
    ).dt.days

    customer_features["recency_days"] = (
        customer_features["recency_days"]
        .clip(lower=0)
    )

    # --------------------------------------------------------
    # Tenure
    # --------------------------------------------------------

    customer_features["tenure_days"] = (
        customer_features["last_purchase_date"]
        - customer_features["signup_date"]
    ).dt.days

    customer_features["tenure_days"] = (
        customer_features["tenure_days"]
        .clip(lower=0)
    )

    # --------------------------------------------------------
    # Existing frequency features
    # --------------------------------------------------------

    customer_features["orders_per_month"] = (
        customer_features["total_orders"]
        / (
            customer_features["tenure_days"] / 30.0
            + 1.0
        )
    )

    customer_features["average_quantity_per_order"] = (
        customer_features["total_quantity"]
        / customer_features["total_orders"].replace(
            0,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Diversity
    # --------------------------------------------------------

    product_diversity = (
        df.groupby("customer_id")["product_id"]
        .nunique()
        .rename("product_diversity")
    )

    customer_features = customer_features.merge(
        product_diversity,
        on="customer_id",
        how="left"
    )

    category_diversity = (
        df.groupby("customer_id")["category"]
        .nunique()
        .rename("category_diversity")
    )

    customer_features = customer_features.merge(
        category_diversity,
        on="customer_id",
        how="left"
    )

    product_name_diversity = (
        df.groupby("customer_id")["product_name"]
        .nunique()
        .rename("product_name_diversity")
    )

    customer_features = customer_features.merge(
        product_name_diversity,
        on="customer_id",
        how="left"
    )

    # --------------------------------------------------------
    # Cancellation rate
    # --------------------------------------------------------

    customer_features["cancellation_rate"] = (
        customer_features["total_cancellations"]
        / customer_features["total_orders"].replace(
            0,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Revenue metrics
    # --------------------------------------------------------

    customer_features["revenue_per_order"] = (
        customer_features["total_revenue"]
        / customer_features["total_orders"].replace(
            0,
            np.nan
        )
    )

    customer_features["revenue_per_unit"] = (
        customer_features["total_revenue"]
        / customer_features["total_quantity"].replace(
            0,
            np.nan
        )
    )

    # --------------------------------------------------------
    # Purchase activity ratio
    # --------------------------------------------------------

    customer_features["purchase_activity_ratio"] = (
        customer_features["total_orders"]
        / (
            customer_features["tenure_days"] + 1
        )
    )

    # --------------------------------------------------------
    # Customer value
    # --------------------------------------------------------

    customer_features["customer_value"] = (
        customer_features["total_revenue"]
        * (
            1
            + customer_features["average_rating"].fillna(0)
            / 5
        )
    )

    print("Base customer features created.")

    return customer_features


# ============================================================
# FEATURE ENGINEERING V2
# ============================================================

def create_v2_features(df):
    print("\n[5/8] Creating Feature Engineering V2 features...")

    df = df.copy()

    # --------------------------------------------------------
    # Safe denominators
    # --------------------------------------------------------

    safe_tenure_months = (
        df["tenure_days"] / 30.0
    ).clip(lower=0.1)

    safe_tenure_years = (
        df["tenure_days"] / 365.0
    ).clip(lower=1 / 365)

    safe_orders = df["total_orders"].replace(
        0,
        np.nan
    )

    safe_quantity = df["total_quantity"].replace(
        0,
        np.nan
    )

    # --------------------------------------------------------
    # 1. Revenue per month
    # --------------------------------------------------------

    df["revenue_per_month"] = (
        df["total_revenue"]
        / safe_tenure_months
    )

    # --------------------------------------------------------
    # 2. Quantity per month
    # --------------------------------------------------------

    df["quantity_per_month"] = (
        df["total_quantity"]
        / safe_tenure_months
    )

    # --------------------------------------------------------
    # 3. Cancellation per order
    # --------------------------------------------------------

    df["cancellation_per_order"] = (
        df["total_cancellations"]
        / safe_orders
    )

    # --------------------------------------------------------
    # 4. Rating-adjusted value
    # --------------------------------------------------------

    df["rating_adjusted_value"] = (
        df["customer_value"]
        * (
            0.5
            + df["average_rating"].fillna(0) / 5
        )
    )

    # --------------------------------------------------------
    # 5. Frequency consistency
    #
    # Lower difference between max/min frequency means
    # more consistent purchase behavior.
    # --------------------------------------------------------

    frequency_range = (
        df["max_purchase_frequency"]
        - df["min_purchase_frequency"]
    )

    df["frequency_consistency"] = (
        1.0
        / (1.0 + frequency_range.abs())
    )

    # --------------------------------------------------------
    # 6. Purchase intensity
    # --------------------------------------------------------

    df["purchase_intensity"] = (
        df["total_orders"]
        / safe_tenure_years
    )

    # --------------------------------------------------------
    # 7. Revenue intensity
    # --------------------------------------------------------

    df["revenue_intensity"] = (
        df["total_revenue"]
        / safe_tenure_years
    )

    # --------------------------------------------------------
    # 8. Quantity intensity
    # --------------------------------------------------------

    df["quantity_intensity"] = (
        df["total_quantity"]
        / safe_tenure_years
    )

    # --------------------------------------------------------
    # 9. Customer value per month
    # --------------------------------------------------------

    df["customer_value_per_month"] = (
        df["customer_value"]
        / safe_tenure_months
    )

    # --------------------------------------------------------
    # 10. Tenure in years
    # --------------------------------------------------------

    df["tenure_years"] = (
        df["tenure_days"] / 365.0
    )

    # --------------------------------------------------------
    # 11. Orders per tenure year
    # --------------------------------------------------------

    df["orders_per_tenure_year"] = (
        df["total_orders"]
        / safe_tenure_years
    )

    # --------------------------------------------------------
    # 12. Revenue per order-month
    # --------------------------------------------------------

    df["revenue_per_order_month"] = (
        df["revenue_per_order"]
        / safe_tenure_months
    )

    # --------------------------------------------------------
    # Interaction features
    # --------------------------------------------------------

    df["revenue_x_frequency"] = (
        df["total_revenue"]
        * (
            1.0
            + df["average_purchase_frequency"].fillna(0)
        )
    )

    df["orders_x_purchase_activity"] = (
        df["total_orders"]
        * df["purchase_activity_ratio"]
    )

    df["value_x_purchase_activity"] = (
        df["customer_value"]
        * df["purchase_activity_ratio"]
    )

    df["cancellation_x_frequency"] = (
        df["cancellation_rate"].fillna(0)
        * (
            1.0
            + df["average_purchase_frequency"].fillna(0)
        )
    )

    # --------------------------------------------------------
    # Diversity ratio
    # --------------------------------------------------------

    df["diversity_ratio"] = (
        (
            df["product_diversity"]
            + df["category_diversity"]
        )
        / safe_orders
    )

    print("Feature Engineering V2 features created.")

    v2_features = [
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
        "diversity_ratio"
    ]

    print("\nNew V2 features:")
    for feature in v2_features:
        print(f"  - {feature}")

    return df


# ============================================================
# BEHAVIORAL BANDS
# ============================================================

def create_behavior_features(df):
    print("\n[6/8] Creating behavioral bands...")

    df = df.copy()

    # --------------------------------------------------------
    # Recency bands
    # --------------------------------------------------------

    df["recency_band"] = pd.cut(
        df["recency_days"],
        bins=[
            -np.inf,
            30,
            60,
            90,
            180,
            np.inf
        ],
        labels=[
            "Very Recent",
            "Recent",
            "Moderate",
            "At Risk",
            "Long Inactive"
        ]
    )

    # --------------------------------------------------------
    # Value bands
    # --------------------------------------------------------

    try:
        df["value_band"] = pd.qcut(
            df["total_revenue"],
            q=4,
            labels=[
                "Low Value",
                "Medium Value",
                "High Value",
                "Very High Value"
            ],
            duplicates="drop"
        )
    except ValueError:
        df["value_band"] = "Medium Value"

    # --------------------------------------------------------
    # Frequency bands
    # --------------------------------------------------------

    df["frequency_band"] = pd.cut(
        df["total_orders"],
        bins=[
            -np.inf,
            1,
            3,
            5,
            np.inf
        ],
        labels=[
            "Low Frequency",
            "Medium Frequency",
            "High Frequency",
            "Very High Frequency"
        ]
    )

    print("Behavioral bands created.")

    return df


# ============================================================
# HANDLE MISSING VALUES
# ============================================================

def handle_feature_missing_values(df):
    print("\n[7/8] Handling feature missing values...")

    df = df.copy()

    numeric_columns = df.select_dtypes(
        include=["number"]
    ).columns

    for column in numeric_columns:
        missing_count = df[column].isna().sum()

        if missing_count > 0:
            median_value = df[column].median()

            if pd.isna(median_value):
                median_value = 0.0

            df[column] = df[column].fillna(
                median_value
            )

            print(
                f"{column}: filled {missing_count} "
                f"missing values."
            )

    categorical_columns = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns

    for column in categorical_columns:
        missing_count = df[column].isna().sum()

        if missing_count > 0:
            df[column] = (
                df[column]
                .astype("object")
                .fillna("Unknown")
            )

            print(
                f"{column}: filled {missing_count} "
                f"missing values."
            )

    return df


# ============================================================
# SAVE FEATURES
# ============================================================

def save_features(df):
    print("\n[8/8] Saving customer features...")

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    preferred_first_columns = [
        "customer_id",
        "age",
        "gender",
        "country",
        "subscription_status"
    ]

    remaining_columns = [
        column
        for column in df.columns
        if column not in preferred_first_columns
    ]

    df = df[
        preferred_first_columns
        + remaining_columns
    ]

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        "Customer features saved successfully."
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )

    return df


# ============================================================
# SUMMARY
# ============================================================

def print_summary(df):
    print("\n")
    print("=" * 70)
    print("FEATURE ENGINEERING V2 COMPLETE")
    print("=" * 70)

    print(f"Customers: {len(df)}")
    print(f"Features : {len(df.columns)}")

    print("\nImportant features:")

    important_features = [
        "recency_days",
        "total_orders",
        "total_quantity",
        "total_revenue",
        "average_order_value",
        "average_rating",
        "total_cancellations",
        "average_purchase_frequency",
        "tenure_days",
        "orders_per_month",
        "purchase_activity_ratio",
        "customer_value",
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
        "diversity_ratio"
    ]

    for feature in important_features:
        if feature in df.columns:
            print(f"  - {feature}")

    print("\nFeature dataset shape:")
    print(df.shape)

    print("\nFirst 5 rows:")
    print(df.head().to_string())

    print("\n" + "=" * 70)
    print("NEXT STEP:")
    print("Run prepare_dataset.py")
    print("Then benchmark all four models again.")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        df = load_data()

        df = prepare_data(df)

        df = create_order_features(df)

        customer_features = create_customer_features(df)

        customer_features = create_v2_features(
            customer_features
        )

        customer_features = create_behavior_features(
            customer_features
        )

        customer_features = handle_feature_missing_values(
            customer_features
        )

        customer_features = save_features(
            customer_features
        )

        print_summary(
            customer_features
        )

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("FEATURE ENGINEERING V2 FAILED")
        print("=" * 70)
        print(f"Error: {error}")
        print("=" * 70)

        raise


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()