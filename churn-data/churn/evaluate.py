"""
Customer Churn Project - Model Evaluation and Audit

This module provides:
- Model loading
- Dataset loading
- Feature validation
- Classification metric calculation
- Evaluation report generation
- Backend handoff audit generation
"""

from pathlib import Path
import pickle
import traceback

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)


# ============================================================================
# PATH CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "churn_dataset.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "churn"
    / "model"
    / "churn_model.pkl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "outputs"
    / "model_evaluation.txt"
)


# ============================================================================
# DISPLAY HELPERS
# ============================================================================

SEPARATOR = "=" * 70


def print_header(title):
    print(SEPARATOR)
    print(title)
    print(SEPARATOR)


# ============================================================================
# BACKEND HANDOFF AUDIT
# ============================================================================

def audit(customers: pd.DataFrame, ranked: pd.DataFrame) -> dict:
    """
    Generate audit information for the backend handoff.

    The audit describes:
    - Total input rows
    - Ranked active customers
    - Number of excluded rows
    - Basic data-quality checks
    - Risk-segment distribution
    - Methodology notes

    This function is intentionally separate from the trained-model
    evaluation logic because run_churn.py uses the explainable
    active-customer prioritization workflow.
    """

    df = customers.copy()

    total_rows = len(df)
    ranked_rows = len(ranked)

    # ------------------------------------------------------------------------
    # Column helpers
    # ------------------------------------------------------------------------

    def find_column(candidates):
        for candidate in candidates:
            if candidate in df.columns:
                return candidate
        return None

    signup_col = find_column(
        [
            "signup_date",
            "sign_up_date",
            "registration_date",
            "customer_signup_date",
        ]
    )

    purchase_col = find_column(
        [
            "last_purchase_date",
            "last_purchase",
            "purchase_date",
        ]
    )

    frequency_col = find_column(
        [
            "purchase_frequency",
            "purchase_freq",
            "frequency",
        ]
    )

    rating_col = find_column(
        [
            "rating",
            "customer_rating",
            "satisfaction_rating",
        ]
    )

    status_col = find_column(
        [
            "subscription_status",
            "status",
        ]
    )

    # ------------------------------------------------------------------------
    # Date validation
    # ------------------------------------------------------------------------

    missing_signup_dates = 0
    invalid_signup_dates = 0
    missing_purchase_dates = 0
    invalid_purchase_dates = 0
    purchase_before_signup = 0
    future_purchase_dates = 0

    signup_dates = None
    purchase_dates = None

    if signup_col:
        signup_dates = pd.to_datetime(
            df[signup_col],
            errors="coerce",
        )

        missing_signup_dates = int(df[signup_col].isna().sum())
        invalid_signup_dates = int(
            signup_dates.isna().sum() - missing_signup_dates
        )

    if purchase_col:
        purchase_dates = pd.to_datetime(
            df[purchase_col],
            errors="coerce",
        )

        missing_purchase_dates = int(df[purchase_col].isna().sum())
        invalid_purchase_dates = int(
            purchase_dates.isna().sum() - missing_purchase_dates
        )

    if signup_dates is not None and purchase_dates is not None:
        valid_dates = signup_dates.notna() & purchase_dates.notna()

        purchase_before_signup = int(
            (
                valid_dates
                & (purchase_dates < signup_dates)
            ).sum()
        )

    # ------------------------------------------------------------------------
    # Frequency validation
    # ------------------------------------------------------------------------

    missing_frequency = 0
    negative_frequency = 0

    if frequency_col:
        frequency_values = pd.to_numeric(
            df[frequency_col],
            errors="coerce",
        )

        missing_frequency = int(frequency_values.isna().sum())
        negative_frequency = int(
            (frequency_values < 0).fillna(False).sum()
        )

    # ------------------------------------------------------------------------
    # Rating validation
    # ------------------------------------------------------------------------

    missing_rating = 0

    if rating_col:
        rating_values = pd.to_numeric(
            df[rating_col],
            errors="coerce",
        )

        missing_rating = int(rating_values.isna().sum())

    # ------------------------------------------------------------------------
    # Active-customer count
    # ------------------------------------------------------------------------

    active_customers = None

    if status_col:
        status_values = (
            df[status_col]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        active_customers = int(
            status_values.isin(
                [
                    "active",
                    "subscribed",
                    "current",
                ]
            ).sum()
        )

    # ------------------------------------------------------------------------
    # Risk-segment distribution
    # ------------------------------------------------------------------------

    segment_distribution = {}

    if "risk_segment" in ranked.columns:
        segment_distribution = {
            str(key): int(value)
            for key, value in ranked["risk_segment"]
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    # ------------------------------------------------------------------------
    # Risk-score information
    # ------------------------------------------------------------------------

    score_statistics = {}

    if "risk_score" in ranked.columns and len(ranked) > 0:
        scores = pd.to_numeric(
            ranked["risk_score"],
            errors="coerce",
        ).dropna()

        if len(scores) > 0:
            score_statistics = {
                "minimum": round(float(scores.min()), 1),
                "maximum": round(float(scores.max()), 1),
                "mean": round(float(scores.mean()), 1),
                "median": round(float(scores.median()), 1),
            }

    # ------------------------------------------------------------------------
    # Audit result
    # ------------------------------------------------------------------------

    diagnostics = {
        "total_input_rows": total_rows,
        "ranked_rows": ranked_rows,
        "excluded_rows": max(total_rows - ranked_rows, 0),
        "active_customers": active_customers,
        "data_quality": {
            "missing_signup_dates": missing_signup_dates,
            "invalid_signup_dates": invalid_signup_dates,
            "missing_purchase_dates": missing_purchase_dates,
            "invalid_purchase_dates": invalid_purchase_dates,
            "purchase_before_signup": purchase_before_signup,
            "future_purchase_dates": future_purchase_dates,
            "missing_purchase_frequency": missing_frequency,
            "negative_purchase_frequency": negative_frequency,
            "missing_rating": missing_rating,
        },
        "risk_segment_distribution": segment_distribution,
        "risk_score_statistics": score_statistics,
        "methodology": {
            "purpose": (
                "Prioritize active customers for outreach using "
                "an explainable risk indicator."
            ),
            "not_a_future_churn_probability": True,
            "score_formula": (
                "100 * (0.55 * recency_percentile + "
                "0.25 * inverse_purchase_frequency_percentile + "
                "0.20 * inverse_rating_percentile)"
            ),
            "thresholds": {
                "high": ">= 70",
                "medium": ">= 40 and < 70",
                "low": "< 40",
            },
            "scoreable_population": "active customers",
        },
    }

    return diagnostics


# ============================================================================
# MODEL LOADING
# ============================================================================

def load_model():
    """
    Load the optimized model package.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found:\n{MODEL_PATH}"
        )

    with open(MODEL_PATH, "rb") as file:
        model_package = pickle.load(file)

    if not isinstance(model_package, dict):
        raise ValueError(
            "The saved model is not a model package dictionary."
        )

    if "model" not in model_package:
        raise KeyError(
            "Model package does not contain the required 'model' key."
        )

    if "features" not in model_package:
        raise KeyError(
            "Model package does not contain the required 'features' key."
        )

    model = model_package["model"]
    feature_columns = model_package["features"]

    prediction_threshold = model_package.get(
        "prediction_threshold",
        0.50,
    )

    print("Model loaded successfully.")
    print(
        f"Prediction threshold: {prediction_threshold:.2f}"
    )

    return (
        model,
        feature_columns,
        prediction_threshold,
        model_package,
    )


# ============================================================================
# DATA LOADING
# ============================================================================

def load_dataset():
    """
    Load the processed churn dataset.
    """

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Churn dataset not found:\n{DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    if "churn" not in df.columns:
        raise KeyError(
            "The dataset does not contain the required 'churn' target column."
        )

    print("Dataset loaded successfully.")
    print(f"Customers loaded: {len(df)}")

    return df


# ============================================================================
# FEATURE VALIDATION
# ============================================================================

def prepare_features(df, feature_columns):
    """
    Prepare the exact feature set expected by the trained model.
    """

    missing_features = [
        feature
        for feature in feature_columns
        if feature not in df.columns
    ]

    if missing_features:
        raise KeyError(
            "The following model features are missing from the dataset:\n"
            + "\n".join(
                f"  - {feature}"
                for feature in missing_features
            )
        )

    X = df[feature_columns].copy()

    for column in X.columns:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    if X.isnull().any().any():
        null_columns = X.columns[
            X.isnull().any()
        ].tolist()

        raise ValueError(
            "Missing/non-numeric values found in model features:\n"
            + "\n".join(
                f"  - {column}"
                for column in null_columns
            )
        )

    print(
        f"Prediction features prepared: {len(feature_columns)}"
    )

    return X


# ============================================================================
# METRIC CALCULATION
# ============================================================================

def calculate_metrics(y_true, y_probability, threshold):
    """
    Calculate classification metrics using the saved threshold.
    """

    y_prediction = (
        y_probability >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        y_true,
        y_prediction,
    )

    precision = precision_score(
        y_true,
        y_prediction,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        y_prediction,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        y_prediction,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_true,
        y_probability,
    )

    cm = confusion_matrix(
        y_true,
        y_prediction,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm,
        "predictions": y_prediction,
    }


# ============================================================================
# MODEL INFORMATION
# ============================================================================

def print_model_information(model_package):
    """
    Display information stored by the optimized training process.
    """

    print()
    print("Model information:")

    if "best_parameters" in model_package:
        print()
        print("Best hyperparameters:")

        for key, value in model_package[
            "best_parameters"
        ].items():
            print(
                f"  {key:<22}: {value}"
            )

    if "cv_roc_auc" in model_package:
        print()
        print(
            "Cross-validation ROC-AUC : "
            f"{model_package['cv_roc_auc']:.4f}"
        )

    if "target_definition" in model_package:
        print()
        print("Target definition:")
        print(
            f"  {model_package['target_definition']}"
        )

    if "threshold_optimization" in model_package:
        optimization = model_package[
            "threshold_optimization"
        ]

        print()
        print("Threshold optimization:")

        if isinstance(optimization, dict):
            if "optimal_threshold" in optimization:
                print(
                    "  Optimal threshold       : "
                    f"{optimization['optimal_threshold']:.2f}"
                )

            if "training_accuracy" in optimization:
                print(
                    "  OOF accuracy            : "
                    f"{optimization['training_accuracy']:.4f}"
                )

            if "training_precision" in optimization:
                print(
                    "  OOF precision           : "
                    f"{optimization['training_precision']:.4f}"
                )

            if "training_recall" in optimization:
                print(
                    "  OOF recall              : "
                    f"{optimization['training_recall']:.4f}"
                )

            if "training_f1" in optimization:
                print(
                    "  OOF F1                  : "
                    f"{optimization['training_f1']:.4f}"
                )


# ============================================================================
# EVALUATION REPORT
# ============================================================================

def create_report(
    metrics,
    threshold,
    model_package,
    total_customers,
):
    """
    Create a readable evaluation report.
    """

    cm = metrics["confusion_matrix"]

    report_lines = []

    report_lines.append(SEPARATOR)
    report_lines.append(
        "CUSTOMER CHURN PROJECT - MODEL EVALUATION REPORT"
    )
    report_lines.append(SEPARATOR)
    report_lines.append("")

    report_lines.append("MODEL CONFIGURATION")
    report_lines.append("-" * 70)
    report_lines.append(
        f"Prediction threshold       : {threshold:.2f}"
    )
    report_lines.append(
        f"Customers evaluated        : {total_customers}"
    )

    if "cv_roc_auc" in model_package:
        report_lines.append(
            "Cross-validation ROC-AUC   : "
            f"{model_package['cv_roc_auc']:.4f}"
        )

    report_lines.append("")

    if "target_definition" in model_package:
        report_lines.append("TARGET DEFINITION")
        report_lines.append("-" * 70)
        report_lines.append(
            str(model_package["target_definition"])
        )
        report_lines.append("")

    report_lines.append("TEST / FULL DATASET METRICS")
    report_lines.append("-" * 70)

    report_lines.append(
        "Accuracy                   : "
        f"{metrics['accuracy']:.4f} "
        f"({metrics['accuracy'] * 100:.2f}%)"
    )

    report_lines.append(
        "Precision                  : "
        f"{metrics['precision']:.4f} "
        f"({metrics['precision'] * 100:.2f}%)"
    )

    report_lines.append(
        "Recall                     : "
        f"{metrics['recall']:.4f} "
        f"({metrics['recall'] * 100:.2f}%)"
    )

    report_lines.append(
        "F1 Score                   : "
        f"{metrics['f1']:.4f} "
        f"({metrics['f1'] * 100:.2f}%)"
    )

    report_lines.append(
        "ROC-AUC                    : "
        f"{metrics['roc_auc']:.4f} "
        f"({metrics['roc_auc'] * 100:.2f}%)"
    )

    report_lines.append("")

    report_lines.append("CONFUSION MATRIX")
    report_lines.append("-" * 70)

    report_lines.append(
        "                 Predicted  Predicted"
    )
    report_lines.append(
        "                 Active     Churned"
    )
    report_lines.append(
        f"Actual Active    {cm[0, 0]:<10} {cm[0, 1]}"
    )
    report_lines.append(
        f"Actual Churned   {cm[1, 0]:<10} {cm[1, 1]}"
    )

    report_lines.append("")

    report_lines.append("INTERPRETATION")
    report_lines.append("-" * 70)

    report_lines.append(
        "Accuracy  : Overall percentage of correct predictions."
    )

    report_lines.append(
        "Precision : Of customers predicted as churned, "
        "percentage actually labeled churned."
    )

    report_lines.append(
        "Recall    : Of customers labeled churned, "
        "percentage correctly identified."
    )

    report_lines.append(
        "F1 Score  : Balance between precision and recall."
    )

    report_lines.append(
        "ROC-AUC   : Ability of the model to rank churned "
        "customers above active customers."
    )

    report_lines.append("")

    report_lines.append("IMPORTANT:")

    report_lines.append(
        "The churn target in this project is a behavioral proxy "
        "based on the recency distribution, not an observed "
        "historical churn event."
    )

    report_lines.append("")

    report_lines.append(SEPARATOR)

    return "\n".join(report_lines)


# ============================================================================
# MAIN
# ============================================================================

def main():

    print_header(
        "CUSTOMER CHURN PROJECT - MODEL EVALUATION"
    )

    try:

        # --------------------------------------------------------------------
        # STEP 1
        # --------------------------------------------------------------------

        print()
        print("[1/6] Loading trained model...")

        (
            model,
            feature_columns,
            prediction_threshold,
            model_package,
        ) = load_model()

        # --------------------------------------------------------------------
        # STEP 2
        # --------------------------------------------------------------------

        print()
        print("[2/6] Loading churn dataset...")

        df = load_dataset()

        # --------------------------------------------------------------------
        # STEP 3
        # --------------------------------------------------------------------

        print()
        print("[3/6] Preparing evaluation features...")

        X = prepare_features(
            df,
            feature_columns,
        )

        y_true = pd.to_numeric(
            df["churn"],
            errors="coerce",
        ).astype(int)

        print(
            f"Evaluation samples prepared: {len(X)}"
        )

        # --------------------------------------------------------------------
        # STEP 4
        # --------------------------------------------------------------------

        print()
        print("[4/6] Generating model probabilities...")

        y_probability = model.predict_proba(X)[:, 1]

        print(
            "Probability predictions generated successfully."
        )

        # --------------------------------------------------------------------
        # STEP 5
        # --------------------------------------------------------------------

        print()
        print("[5/6] Calculating evaluation metrics...")

        metrics = calculate_metrics(
            y_true,
            y_probability,
            prediction_threshold,
        )

        print(
            "Evaluation metrics calculated successfully."
        )

        # --------------------------------------------------------------------
        # STEP 6
        # --------------------------------------------------------------------

        print()
        print("[6/6] Saving evaluation report...")

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        report = create_report(
            metrics=metrics,
            threshold=prediction_threshold,
            model_package=model_package,
            total_customers=len(df),
        )

        with open(
            OUTPUT_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(report)

        # --------------------------------------------------------------------
        # CONSOLE RESULTS
        # --------------------------------------------------------------------

        print()
        print_header(
            "MODEL EVALUATION COMPLETE"
        )

        print()
        print("Evaluation threshold:")
        print(
            f"  {prediction_threshold:.2f}"
        )

        print()
        print("Evaluation metrics:")

        print(
            "  Accuracy   : "
            f"{metrics['accuracy']:.4f} "
            f"({metrics['accuracy'] * 100:.2f}%)"
        )

        print(
            "  Precision  : "
            f"{metrics['precision']:.4f} "
            f"({metrics['precision'] * 100:.2f}%)"
        )

        print(
            "  Recall     : "
            f"{metrics['recall']:.4f} "
            f"({metrics['recall'] * 100:.2f}%)"
        )

        print(
            "  F1 Score   : "
            f"{metrics['f1']:.4f} "
            f"({metrics['f1'] * 100:.2f}%)"
        )

        print(
            "  ROC-AUC    : "
            f"{metrics['roc_auc']:.4f} "
            f"({metrics['roc_auc'] * 100:.2f}%)"
        )

        print()
        print("Confusion matrix:")

        cm = metrics["confusion_matrix"]

        print()
        print("                 Predicted")
        print("                 Active  Churned")
        print(
            f"Actual Active    {cm[0, 0]:>6}  {cm[0, 1]:>7}"
        )
        print(
            f"Actual Churned   {cm[1, 0]:>6}  {cm[1, 1]:>7}"
        )

        print()
        print("Classification report:")
        print()

        print(
            classification_report(
                y_true,
                metrics["predictions"],
                target_names=[
                    "Active",
                    "Churned",
                ],
                zero_division=0,
            )
        )

        print("Model information:")
        print_model_information(
            model_package
        )

        print()
        print("Evaluation report saved successfully:")
        print(
            OUTPUT_PATH
        )

        print()
        print_header(
            "OUTPUT READY"
        )

    except Exception as error:

        print()
        print_header(
            "MODEL EVALUATION FAILED"
        )

        print(
            f"Error: {error}"
        )

        print()
        traceback.print_exc()


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()