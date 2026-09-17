"""
Customer Churn Prediction & Sales Forecasting
V2 Business Segmentation Module

Purpose:
    Convert ML churn predictions into actionable business segments,
    retention priorities, priority scores, and recommended actions.

Input:
    churn-data/outputs/churn_predictions.csv

Output:
    churn-data/outputs/customer_segments.csv
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

CURRENT_FILE = Path(__file__).resolve()

# Project root:
# customer-churn-sales-forecasting/
PROJECT_ROOT = CURRENT_FILE.parents[2]

INPUT_FILE = PROJECT_ROOT / "churn-data" / "outputs" / "churn_predictions.csv"
OUTPUT_DIR = PROJECT_ROOT / "churn-data" / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "customer_segments.csv"


# ============================================================================
# REQUIRED COLUMNS
# ============================================================================

REQUIRED_COLUMNS = [
    "customer_id",
    "churn_probability",
    "risk_score",
    "risk_segment",
    "risk_level",
    "customer_value",
    "total_orders",
    "total_revenue",
    "revenue_at_risk",
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_section(title):
    """Print a formatted section heading."""
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def validate_input(df):
    """Validate required input columns."""

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR: Missing required columns:")
        for column in missing_columns:
            print(f"  - {column}")

        sys.exit(1)

    print("All required prediction columns are available.")


# ============================================================================
# BUSINESS SEGMENTATION
# ============================================================================

def assign_customer_segment(row):
    """
    Assign business-facing customer segment.

    CRITICAL_RETENTION:
        Very high churn probability.

    HIGH_RISK_RETENTION:
        High churn probability.

    ENGAGEMENT:
        Moderate churn probability.

    LOYAL_ACTIVE:
        Lower churn probability.
    """

    probability = float(row["churn_probability"])

    if probability >= 0.75:
        return "CRITICAL_RETENTION"

    elif probability >= 0.50:
        return "HIGH_RISK_RETENTION"

    elif probability >= 0.25:
        return "ENGAGEMENT"

    else:
        return "LOYAL_ACTIVE"


# ============================================================================
# RETENTION PRIORITY
# ============================================================================

def assign_retention_priority(row):
    """
    Assign operational retention priority.

    Priority is based primarily on churn risk and secondarily
    on revenue at risk.
    """

    probability = float(row["churn_probability"])
    revenue_at_risk = float(row["revenue_at_risk"])

    if probability >= 0.75:
        return "URGENT"

    elif probability >= 0.50:
        if revenue_at_risk >= 1000:
            return "URGENT"
        return "HIGH"

    elif probability >= 0.25:
        if revenue_at_risk >= 1000:
            return "HIGH"
        return "MEDIUM"

    else:
        return "LOW"


# ============================================================================
# RECOMMENDED BUSINESS ACTION
# ============================================================================

def assign_recommended_action(row):
    """
    Generate an explainable retention recommendation.
    """

    segment = row["customer_segment"]
    revenue_at_risk = float(row["revenue_at_risk"])
    days_since_purchase = float(row["days_since_purchase"])

    if segment == "CRITICAL_RETENTION":

        if revenue_at_risk >= 1000:
            return "Immediate high-value retention intervention"

        elif days_since_purchase >= 1000:
            return "Immediate reactivation campaign"

        else:
            return "Immediate retention intervention"

    elif segment == "HIGH_RISK_RETENTION":

        if revenue_at_risk >= 1000:
            return "Priority high-value retention campaign"

        elif days_since_purchase >= 750:
            return "Priority reactivation campaign"

        else:
            return "Targeted retention campaign"

    elif segment == "ENGAGEMENT":

        if days_since_purchase >= 500:
            return "Personalized re-engagement campaign"

        return "Personalized engagement campaign"

    else:

        return "Maintain relationship and encourage repeat purchase"


# ============================================================================
# PRIORITY SCORE
# ============================================================================

def calculate_priority_score(df):
    """
    Calculate a 0-100 business priority score.

    Components:
        70% -> churn probability
        30% -> normalized revenue at risk

    This score is for operational prioritization and is NOT the ML
    probability itself.
    """

    probability_component = (
        df["churn_probability"].clip(0, 1) * 70
    )

    revenue = df["revenue_at_risk"].clip(lower=0)

    max_revenue = revenue.max()

    if max_revenue > 0:
        revenue_component = (
            revenue / max_revenue
        ) * 30
    else:
        revenue_component = pd.Series(
            0,
            index=df.index
        )

    priority_score = (
        probability_component +
        revenue_component
    )

    return priority_score.clip(0, 100)


# ============================================================================
# MAIN PROCESSING
# ============================================================================

def main():

    print_section(
        "CUSTOMER CHURN PROJECT - V2 BUSINESS SEGMENTATION"
    )

    # ------------------------------------------------------------------------
    # STEP 1 - LOAD PREDICTIONS
    # ------------------------------------------------------------------------

    print("\n[1/8] Loading V2 ML predictions...")

    print(f"Input file: {INPUT_FILE}")

    if not INPUT_FILE.exists():

        print()
        print("ERROR: Prediction file not found.")
        print()
        print("Run this first:")
        print("  python churn\\predict.py")
        print()

        sys.exit(1)

    df = pd.read_csv(INPUT_FILE)

    print("Prediction file loaded successfully.")
    print(f"Customers: {len(df)}")
    print(f"Columns : {len(df.columns)}")

    # ------------------------------------------------------------------------
    # STEP 2 - VALIDATE
    # ------------------------------------------------------------------------

    print("\n[2/8] Validating prediction data...")

    validate_input(df)

    # ------------------------------------------------------------------------
    # STEP 3 - NUMERIC CLEANING
    # ------------------------------------------------------------------------

    print("\n[3/8] Preparing business metrics...")

    numeric_columns = [
        "churn_probability",
        "risk_score",
        "customer_value",
        "total_orders",
        "total_revenue",
        "revenue_at_risk",
        "days_since_purchase",
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    # Keep probability in valid range.
    df["churn_probability"] = (
        df["churn_probability"]
        .clip(0, 1)
    )

    # ------------------------------------------------------------------------
    # STEP 4 - CUSTOMER SEGMENT
    # ------------------------------------------------------------------------

    print("\n[4/8] Assigning business customer segments...")

    df["customer_segment"] = df.apply(
        assign_customer_segment,
        axis=1
    )

    print("Customer segmentation completed.")

    # ------------------------------------------------------------------------
    # STEP 5 - RETENTION PRIORITY
    # ------------------------------------------------------------------------

    print("\n[5/8] Assigning retention priorities...")

    df["retention_priority"] = df.apply(
        assign_retention_priority,
        axis=1
    )

    print("Retention priorities assigned.")

    # ------------------------------------------------------------------------
    # STEP 6 - BUSINESS ACTIONS
    # ------------------------------------------------------------------------

    print("\n[6/8] Generating recommended retention actions...")

    df["recommended_action"] = df.apply(
        assign_recommended_action,
        axis=1
    )

    # ------------------------------------------------------------------------
    # STEP 7 - PRIORITY SCORE AND FLAGS
    # ------------------------------------------------------------------------

    print("\n[7/8] Calculating priority scores and business flags...")

    df["priority_score"] = calculate_priority_score(df)

    # Percentage representation of churn probability.
    df["churn_probability_percent"] = (
        df["churn_probability"] * 100
    ).round(2)

    # Immediate attention flag.
    df["needs_immediate_attention"] = (
        df["retention_priority"] == "URGENT"
    )

    # High-value risk flag.
    revenue_median = df["revenue_at_risk"].median()

    df["high_value_risk"] = (
        df["risk_segment"].isin(["CRITICAL", "HIGH"])
        &
        (df["revenue_at_risk"] >= revenue_median)
    )

    # Sort by operational priority.
    priority_order = {
        "URGENT": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
    }

    df["_priority_order"] = (
        df["retention_priority"]
        .map(priority_order)
        .fillna(99)
    )

    df = df.sort_values(
        by=[
            "_priority_order",
            "priority_score",
            "revenue_at_risk",
        ],
        ascending=[
            True,
            False,
            False,
        ]
    ).reset_index(drop=True)

    # Assign business priority rank.
    df["priority_rank"] = (
        np.arange(len(df)) + 1
    )

    # Remove internal sorting helper.
    df.drop(
        columns=["_priority_order"],
        inplace=True
    )

    # ------------------------------------------------------------------------
    # OUTPUT COLUMN ORDER
    # ------------------------------------------------------------------------

    preferred_columns = [
        "priority_rank",
        "customer_id",

        "customer_segment",
        "retention_priority",

        "churn_probability",
        "churn_probability_percent",

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

        "priority_score",

        "recommended_action",

        "needs_immediate_attention",
        "high_value_risk",

        "age",
        "country",
        "subscription_status",

        "average_order_value",
        "total_cancellations",

        "product_diversity",
        "category_diversity",

        "tenure_days",
        "orders_per_month",
    ]

    final_columns = [
        column
        for column in preferred_columns
        if column in df.columns
    ]

    # Add any remaining columns after the preferred business columns.
    remaining_columns = [
        column
        for column in df.columns
        if column not in final_columns
    ]

    final_columns.extend(remaining_columns)

    df = df[final_columns]

    # ------------------------------------------------------------------------
    # STEP 8 - SAVE
    # ------------------------------------------------------------------------

    print("\n[8/8] Saving V2 business segmentation...")

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    # ------------------------------------------------------------------------
    # BUSINESS SUMMARY
    # ------------------------------------------------------------------------

    print()
    print("-" * 70)
    print("CUSTOMER SEGMENT DISTRIBUTION")
    print("-" * 70)

    segment_counts = (
        df["customer_segment"]
        .value_counts()
    )

    for segment in [
        "LOYAL_ACTIVE",
        "ENGAGEMENT",
        "HIGH_RISK_RETENTION",
        "CRITICAL_RETENTION",
    ]:

        count = int(
            segment_counts.get(segment, 0)
        )

        percentage = (
            count / len(df) * 100
            if len(df) > 0
            else 0
        )

        print(
            f"{segment:<25}: "
            f"{count:>4} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print("-" * 70)
    print("RETENTION PRIORITY DISTRIBUTION")
    print("-" * 70)

    priority_counts = (
        df["retention_priority"]
        .value_counts()
    )

    for priority in [
        "URGENT",
        "HIGH",
        "MEDIUM",
        "LOW",
    ]:

        count = int(
            priority_counts.get(priority, 0)
        )

        percentage = (
            count / len(df) * 100
            if len(df) > 0
            else 0
        )

        print(
            f"{priority:<10}: "
            f"{count:>4} "
            f"({percentage:>6.2f}%)"
        )

    print()
    print("-" * 70)
    print("BUSINESS METRICS")
    print("-" * 70)

    total_revenue_at_risk = (
        df["revenue_at_risk"].sum()
    )

    urgent_revenue_at_risk = (
        df.loc[
            df["retention_priority"] == "URGENT",
            "revenue_at_risk"
        ].sum()
    )

    high_priority_revenue_at_risk = (
        df.loc[
            df["retention_priority"].isin(
                ["URGENT", "HIGH"]
            ),
            "revenue_at_risk"
        ].sum()
    )

    print(
        f"Total Revenue at Risk       : "
        f"{total_revenue_at_risk:,.2f}"
    )

    print(
        f"Urgent Revenue at Risk      : "
        f"{urgent_revenue_at_risk:,.2f}"
    )

    print(
        f"Urgent + High Revenue Risk  : "
        f"{high_priority_revenue_at_risk:,.2f}"
    )

    print(
        f"Immediate Attention Customers: "
        f"{df['needs_immediate_attention'].sum()}"
    )

    print(
        f"High-Value Risk Customers   : "
        f"{df['high_value_risk'].sum()}"
    )

    # ------------------------------------------------------------------------
    # TOP CUSTOMERS
    # ------------------------------------------------------------------------

    print()
    print("-" * 70)
    print("TOP 10 RETENTION PRIORITIES")
    print("-" * 70)

    display_columns = [
        "priority_rank",
        "customer_id",
        "customer_segment",
        "retention_priority",
        "churn_probability_percent",
        "risk_score",
        "revenue_at_risk",
        "priority_score",
        "recommended_action",
    ]

    available_display_columns = [
        column
        for column in display_columns
        if column in df.columns
    ]

    print(
        df[available_display_columns]
        .head(10)
        .to_string(index=False)
    )

    # ------------------------------------------------------------------------
    # FINAL SUMMARY
    # ------------------------------------------------------------------------

    print()
    print("=" * 70)
    print("V2 BUSINESS SEGMENTATION COMPLETE")
    print("=" * 70)

    print()
    print(f"Customers processed : {len(df)}")
    print(f"Output columns      : {len(df.columns)}")

    print()
    print("Output file:")
    print(f"  {OUTPUT_FILE}")

    print()
    print("Business output contains:")
    print("  - Customer segment")
    print("  - Retention priority")
    print("  - Churn probability")
    print("  - Risk score")
    print("  - Revenue at risk")
    print("  - Priority score")
    print("  - Recommended retention action")
    print("  - Immediate attention flag")
    print("  - High-value risk flag")

    print()
    print("ML → Business Segmentation pipeline is ready.")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()