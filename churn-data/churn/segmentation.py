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
    "outputs",
    "churn_predictions.csv"
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "ml",
    "outputs"
)

OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "customer_segments.csv"
)


# ============================================================
# LOAD PREDICTIONS
# ============================================================

def load_predictions():
    print("=" * 70)
    print("CUSTOMER CHURN PROJECT - CUSTOMER SEGMENTATION")
    print("=" * 70)

    print("\n[1/6] Loading churn predictions...")
    print(f"Input file: {INPUT_FILE}")

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"\nChurn predictions file not found.\n"
            f"Expected location:\n{INPUT_FILE}\n\n"
            f"Run predict.py first."
        )

    df = pd.read_csv(INPUT_FILE)

    print("Churn predictions loaded successfully.")
    print(f"Customers: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    return df


# ============================================================
# VALIDATE DATA
# ============================================================

def validate_data(df):
    print("\n[2/6] Validating prediction data...")

    required_columns = [
        "customer_id",
        "churn_probability",
        "risk_level",
        "revenue_at_risk"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"\nRequired columns are missing:\n"
            f"{missing_columns}\n\n"
            f"Available columns:\n"
            f"{list(df.columns)}"
        )

    # Convert numerical columns.
    df["churn_probability"] = pd.to_numeric(
        df["churn_probability"],
        errors="coerce"
    )

    df["revenue_at_risk"] = pd.to_numeric(
        df["revenue_at_risk"],
        errors="coerce"
    )

    df["total_revenue"] = pd.to_numeric(
        df.get(
            "total_revenue",
            pd.Series(0, index=df.index)
        ),
        errors="coerce"
    )

    df["total_orders"] = pd.to_numeric(
        df.get(
            "total_orders",
            pd.Series(0, index=df.index)
        ),
        errors="coerce"
    )

    df["total_cancellations"] = pd.to_numeric(
        df.get(
            "total_cancellations",
            pd.Series(0, index=df.index)
        ),
        errors="coerce"
    )

    df = df.replace(
        [np.inf, -np.inf],
        np.nan
    )

    df["churn_probability"] = (
        df["churn_probability"]
        .fillna(0)
        .clip(0, 1)
    )

    df["revenue_at_risk"] = (
        df["revenue_at_risk"]
        .fillna(0)
        .clip(lower=0)
    )

    print("Prediction data validated.")

    return df


# ============================================================
# ASSIGN BUSINESS SEGMENT
# ============================================================

def assign_customer_segment(row):
    probability = row["churn_probability"]
    revenue_at_risk = row["revenue_at_risk"]

    # --------------------------------------------------------
    # CRITICAL
    # --------------------------------------------------------

    if probability >= 0.75:
        return "CRITICAL_RETENTION"

    # --------------------------------------------------------
    # HIGH RISK
    # --------------------------------------------------------

    if probability >= 0.50:
        return "HIGH_RISK_RETENTION"

    # --------------------------------------------------------
    # MEDIUM RISK
    # --------------------------------------------------------

    if probability >= 0.25:
        return "ENGAGEMENT"

    # --------------------------------------------------------
    # LOW RISK
    # --------------------------------------------------------

    return "LOYAL_ACTIVE"


# ============================================================
# ASSIGN ACTION
# ============================================================

def assign_action(row):
    segment = row["customer_segment"]
    revenue_at_risk = row["revenue_at_risk"]

    if segment == "CRITICAL_RETENTION":
        if revenue_at_risk >= 1000:
            return "Immediate high-value retention intervention"
        else:
            return "Immediate retention intervention"

    if segment == "HIGH_RISK_RETENTION":
        if revenue_at_risk >= 1000:
            return "Priority retention campaign"
        else:
            return "Targeted retention campaign"

    if segment == "ENGAGEMENT":
        return "Personalized engagement campaign"

    return "Maintain relationship and encourage repeat purchase"


# ============================================================
# ASSIGN PRIORITY
# ============================================================

def calculate_priority_score(row):
    probability = row["churn_probability"]
    revenue_at_risk = row["revenue_at_risk"]

    # --------------------------------------------------------
    # Normalize revenue-at-risk.
    #
    # We use log scaling so a very large customer does not
    # completely dominate the score.
    # --------------------------------------------------------

    revenue_component = np.log1p(
        max(revenue_at_risk, 0)
    )

    # Churn probability receives the strongest weight.
    probability_component = (
        probability * 70
    )

    revenue_component = (
        min(revenue_component / 10, 1)
        * 30
    )

    score = (
        probability_component
        + revenue_component
    )

    return round(
        min(score, 100),
        2
    )


# ============================================================
# CREATE CUSTOMER SEGMENTS
# ============================================================

def create_segments(df):
    print("\n[3/6] Creating customer segments...")

    df["customer_segment"] = df.apply(
        assign_customer_segment,
        axis=1
    )

    df["recommended_action"] = df.apply(
        assign_action,
        axis=1
    )

    df["priority_score"] = df.apply(
        calculate_priority_score,
        axis=1
    )

    # --------------------------------------------------------
    # Priority rank
    # --------------------------------------------------------

    df = df.sort_values(
        by=[
            "priority_score",
            "revenue_at_risk",
            "churn_probability"
        ],
        ascending=[
            False,
            False,
            False
        ]
    ).reset_index(drop=True)

    df["priority_rank"] = (
        df.index + 1
    )

    print("Customer segments created.")

    return df


# ============================================================
# ADD BUSINESS FLAGS
# ============================================================

def create_business_flags(df):
    print("\n[4/6] Creating business priority flags...")

    # --------------------------------------------------------
    # Immediate attention
    # --------------------------------------------------------

    df["needs_immediate_attention"] = (
        df["customer_segment"]
        == "CRITICAL_RETENTION"
    )

    # --------------------------------------------------------
    # High-value risk
    # --------------------------------------------------------

    revenue_median = df[
        "revenue_at_risk"
    ].median()

    if pd.isna(revenue_median):
        revenue_median = 0

    df["high_value_risk"] = (
        (
            df["customer_segment"].isin(
                [
                    "CRITICAL_RETENTION",
                    "HIGH_RISK_RETENTION"
                ]
            )
        )
        &
        (
            df["revenue_at_risk"]
            >= revenue_median
        )
    )

    # --------------------------------------------------------
    # Retention priority
    # --------------------------------------------------------

    df["retention_priority"] = np.select(
        [
            df["customer_segment"]
            == "CRITICAL_RETENTION",

            df["customer_segment"]
            == "HIGH_RISK_RETENTION",

            df["customer_segment"]
            == "ENGAGEMENT"
        ],
        [
            "URGENT",
            "HIGH",
            "MEDIUM"
        ],
        default="LOW"
    )

    print("Business flags created.")

    return df


# ============================================================
# SELECT FINAL COLUMNS
# ============================================================

def prepare_output(df):
    print("\n[5/6] Preparing final segmentation output...")

    preferred_columns = [
        "priority_rank",
        "customer_id",
        "customer_segment",
        "retention_priority",
        "churn_probability",
        "churn_probability_percent",
        "risk_level",
        "customer_value",
        "revenue_at_risk",
        "priority_score",
        "recommended_action",
        "needs_immediate_attention",
        "high_value_risk",
        "age",
        "country",
        "subscription_status",
        "total_orders",
        "total_revenue",
        "average_order_value",
        "total_cancellations",
        "product_diversity",
        "category_diversity",
        "tenure_days",
        "orders_per_month"
    ]

    available_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    output = df[
        available_columns
    ].copy()

    return output


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(df):
    print("\n[6/6] Saving customer segments...")

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"Customer segmentation saved successfully."
    )

    print(
        f"Output file: {OUTPUT_FILE}"
    )


# ============================================================
# PRINT SUMMARY
# ============================================================

def print_summary(df):
    print("\n")
    print("=" * 70)
    print("CUSTOMER SEGMENTATION COMPLETE")
    print("=" * 70)

    total_customers = len(df)

    # --------------------------------------------------------
    # Segment distribution
    # --------------------------------------------------------

    print("\nCustomer segment distribution:")

    segment_order = [
        "LOYAL_ACTIVE",
        "ENGAGEMENT",
        "HIGH_RISK_RETENTION",
        "CRITICAL_RETENTION"
    ]

    for segment in segment_order:
        count = (
            df["customer_segment"]
            == segment
        ).sum()

        percentage = (
            count / total_customers * 100
            if total_customers > 0
            else 0
        )

        print(
            f"  {segment:<25} "
            f"{count:>5} "
            f"({percentage:>6.2f}%)"
        )

    # --------------------------------------------------------
    # Retention priority distribution
    # --------------------------------------------------------

    print("\nRetention priority:")

    priority_order = [
        "URGENT",
        "HIGH",
        "MEDIUM",
        "LOW"
    ]

    for priority in priority_order:
        count = (
            df["retention_priority"]
            == priority
        ).sum()

        print(
            f"  {priority:<10}: {count}"
        )

    # --------------------------------------------------------
    # Revenue at risk
    # --------------------------------------------------------

    total_revenue_at_risk = (
        df["revenue_at_risk"]
        .sum()
    )

    critical_revenue = (
        df.loc[
            df["customer_segment"]
            == "CRITICAL_RETENTION",
            "revenue_at_risk"
        ].sum()
    )

    high_risk_revenue = (
        df.loc[
            df["customer_segment"].isin(
                [
                    "CRITICAL_RETENTION",
                    "HIGH_RISK_RETENTION"
                ]
            ),
            "revenue_at_risk"
        ].sum()
    )

    print("\nRevenue at risk:")
    print(
        f"  Total: "
        f"{total_revenue_at_risk:,.2f}"
    )

    print(
        f"  Critical customers: "
        f"{critical_revenue:,.2f}"
    )

    print(
        f"  High + Critical: "
        f"{high_risk_revenue:,.2f}"
    )

    # --------------------------------------------------------
    # Top priority customers
    # --------------------------------------------------------

    print("\nTop 10 priority customers:")

    display_columns = [
        "priority_rank",
        "customer_id",
        "customer_segment",
        "churn_probability_percent",
        "revenue_at_risk",
        "priority_score",
        "recommended_action"
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    print(
        df[
            available_display_columns
        ].head(10).to_string(
            index=False
        )
    )

    print("\nOutput file:")
    print(OUTPUT_FILE)

    print("\n" + "=" * 70)
    print("MEMBER 2 CHURN PIPELINE COMPLETE")
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main():
    try:
        # Step 1
        df = load_predictions()

        # Step 2
        df = validate_data(df)

        # Step 3
        df = create_segments(df)

        # Step 4
        df = create_business_flags(df)

        # Step 5
        df = prepare_output(df)

        # Step 6
        save_output(df)

        # Summary
        print_summary(df)

    except Exception as e:
        print("\n")
        print("=" * 70)
        print("CUSTOMER SEGMENTATION FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        print("=" * 70)

        raise


# ============================================================
# RUN PROGRAM
# ============================================================

if __name__ == "__main__":
    main()