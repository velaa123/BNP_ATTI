"""
Customer Churn Project - XGBoost Training

Trains and tunes an XGBoost classifier for customer churn prediction.

The model uses the same churn_dataset.csv and the same 80/20
stratified split used by the current Random Forest model so that
the results can be compared fairly.
"""

from pathlib import Path
import pickle
import warnings

import numpy as np
import pandas as pd

from sklearn.model_selection import (
    train_test_split,
    StratifiedKFold,
    RandomizedSearchCV,
)
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

from xgboost import XGBClassifier

warnings.filterwarnings("ignore")


# ============================================================================
# PATHS
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
    / "xgboost_churn_model.pkl"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "outputs"
    / "xgboost_evaluation.txt"
)


# ============================================================================
# FEATURES
# ============================================================================

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
]


# ============================================================================
# CONFIGURATION
# ============================================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20

N_ITER_SEARCH = 40
CV_FOLDS = 5


# ============================================================================
# LOAD DATA
# ============================================================================

def load_data():

    print()
    print("[1/7] Loading churn dataset...")

    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found:\n{DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    print(f"Dataset loaded successfully.")
    print(f"Customers: {len(df)}")

    missing_features = [
        feature
        for feature in MODEL_FEATURES
        if feature not in df.columns
    ]

    if missing_features:
        raise KeyError(
            "Missing model features:\n"
            + "\n".join(
                f"  - {feature}"
                for feature in missing_features
            )
        )

    if "churn" not in df.columns:
        raise KeyError(
            "Target column 'churn' not found."
        )

    return df


# ============================================================================
# PREPARE DATA
# ============================================================================

def prepare_data(df):

    print()
    print("[2/7] Preparing model features...")

    X = df[MODEL_FEATURES].copy()
    y = df["churn"].astype(int)

    for column in X.columns:
        X[column] = pd.to_numeric(
            X[column],
            errors="coerce"
        )

    if X.isnull().any().any():
        raise ValueError(
            "Missing/non-numeric values detected in model features."
        )

    print(f"Features: {len(MODEL_FEATURES)}")
    print(f"Samples: {len(X)}")

    print()
    print("Target distribution:")

    target_counts = y.value_counts().sort_index()

    for target_value, count in target_counts.items():

        label = (
            "Active"
            if target_value == 0
            else "Churned"
        )

        percentage = (
            count / len(y) * 100
        )

        print(
            f"  {label:<10}: "
            f"{count:>4} "
            f"({percentage:>6.2f}%)"
        )

    return X, y


# ============================================================================
# TRAIN / TEST SPLIT
# ============================================================================

def split_data(X, y):

    print()
    print("[3/7] Creating stratified train/test split...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )

    print(
        f"Training samples: {len(X_train)}"
    )

    print(
        f"Testing samples : {len(X_test)}"
    )

    return X_train, X_test, y_train, y_test


# ============================================================================
# XGBOOST TUNING
# ============================================================================

def tune_xgboost(
    X_train,
    y_train,
):

    print()
    print("[4/7] Tuning XGBoost hyperparameters...")

    # ------------------------------------------------------------------------
    # Calculate positive-class weighting.
    # ------------------------------------------------------------------------

    negative_count = int(
        (y_train == 0).sum()
    )

    positive_count = int(
        (y_train == 1).sum()
    )

    scale_pos_weight = (
        negative_count / positive_count
    )

    print(
        f"scale_pos_weight: "
        f"{scale_pos_weight:.4f}"
    )

    # ------------------------------------------------------------------------
    # Base model
    # ------------------------------------------------------------------------

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        tree_method="hist",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )

    # ------------------------------------------------------------------------
    # Parameter search space
    # ------------------------------------------------------------------------

    parameter_distributions = {

        "n_estimators": [
            200,
            300,
            400,
            500,
            600,
            800,
        ],

        "max_depth": [
            2,
            3,
            4,
            5,
            6,
            7,
        ],

        "learning_rate": [
            0.01,
            0.02,
            0.03,
            0.05,
            0.08,
            0.10,
            0.15,
        ],

        "min_child_weight": [
            1,
            2,
            3,
            5,
            7,
            10,
        ],

        "subsample": [
            0.70,
            0.80,
            0.90,
            1.00,
        ],

        "colsample_bytree": [
            0.70,
            0.80,
            0.90,
            1.00,
        ],

        "gamma": [
            0,
            0.05,
            0.10,
            0.20,
            0.30,
        ],

        "reg_alpha": [
            0,
            0.01,
            0.05,
            0.10,
            0.50,
        ],

        "reg_lambda": [
            0.5,
            1,
            1.5,
            2,
            3,
        ],

        "scale_pos_weight": [
            1.0,
            scale_pos_weight,
            scale_pos_weight * 0.75,
            scale_pos_weight * 1.25,
        ],
    }

    cv = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )

    search = RandomizedSearchCV(
        estimator=model,
        param_distributions=parameter_distributions,
        n_iter=N_ITER_SEARCH,
        scoring="roc_auc",
        cv=cv,
        verbose=1,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        refit=True,
    )

    search.fit(
        X_train,
        y_train,
    )

    print()
    print("XGBoost tuning completed.")

    print()
    print("Best parameters:")

    for key, value in search.best_params_.items():

        print(
            f"  {key:<20}: {value}"
        )

    print()
    print(
        f"Best CV ROC-AUC: "
        f"{search.best_score_:.4f}"
    )

    return (
        search.best_estimator_,
        search.best_score_,
        search.best_params_,
    )


# ============================================================================
# THRESHOLD OPTIMIZATION
# ============================================================================

def optimize_threshold(
    model,
    X_train,
    y_train,
):

    print()
    print("[5/7] Optimizing prediction threshold...")

    probabilities = model.predict_proba(
        X_train
    )[:, 1]

    thresholds = np.arange(
        0.20,
        0.81,
        0.01
    )

    results = []

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_train,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_train,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y_train,
            predictions,
            zero_division=0,
        )

        accuracy = accuracy_score(
            y_train,
            predictions,
        )

        results.append(
            {
                "threshold": threshold,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    results_df = pd.DataFrame(results)

    # ------------------------------------------------------------------------
    # Select threshold using F1.
    #
    # Ties:
    # 1. Higher F1
    # 2. Higher recall
    # 3. Higher precision
    # 4. Lower threshold
    # ------------------------------------------------------------------------

    results_df = results_df.sort_values(
        by=[
            "f1",
            "recall",
            "precision",
            "threshold",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    )

    best_row = results_df.iloc[0]

    optimal_threshold = float(
        best_row["threshold"]
    )

    print()
    print(
        f"Optimal threshold: "
        f"{optimal_threshold:.2f}"
    )

    print(
        f"OOF-like training accuracy : "
        f"{best_row['accuracy']:.4f}"
    )

    print(
        f"Training precision         : "
        f"{best_row['precision']:.4f}"
    )

    print(
        f"Training recall            : "
        f"{best_row['recall']:.4f}"
    )

    print(
        f"Training F1                : "
        f"{best_row['f1']:.4f}"
    )

    return optimal_threshold, results_df


# ============================================================================
# TEST EVALUATION
# ============================================================================

def evaluate_model(
    model,
    X_test,
    y_test,
    threshold,
):

    print()
    print("[6/7] Evaluating XGBoost on untouched test set...")

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities >= threshold
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    cm = confusion_matrix(
        y_test,
        predictions,
    )

    print()
    print("=" * 70)
    print("XGBOOST TEST RESULTS")
    print("=" * 70)

    print()
    print(
        f"Accuracy   : "
        f"{accuracy:.4f} "
        f"({accuracy * 100:.2f}%)"
    )

    print(
        f"Precision  : "
        f"{precision:.4f} "
        f"({precision * 100:.2f}%)"
    )

    print(
        f"Recall     : "
        f"{recall:.4f} "
        f"({recall * 100:.2f}%)"
    )

    print(
        f"F1 Score   : "
        f"{f1:.4f} "
        f"({f1 * 100:.2f}%)"
    )

    print(
        f"ROC-AUC    : "
        f"{roc_auc:.4f} "
        f"({roc_auc * 100:.2f}%)"
    )

    print()
    print("Confusion matrix:")

    print()
    print("                 Predicted")
    print("                 Active  Churned")

    print(
        f"Actual Active    "
        f"{cm[0, 0]:>6}  "
        f"{cm[0, 1]:>7}"
    )

    print(
        f"Actual Churned   "
        f"{cm[1, 0]:>6}  "
        f"{cm[1, 1]:>7}"
    )

    print()
    print("Classification report:")
    print()

    print(
        classification_report(
            y_test,
            predictions,
            target_names=[
                "Active",
                "Churned",
            ],
            zero_division=0,
        )
    )

    train_probabilities = model.predict_proba(
        X_test
    )[:, 1]

    metrics = {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "confusion_matrix": cm.tolist(),
    }

    return metrics


# ============================================================================
# SAVE MODEL
# ============================================================================

def save_model(
    model,
    best_params,
    cv_roc_auc,
    threshold,
    test_metrics,
):

    print()
    print("[7/7] Saving XGBoost model...")

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_package = {

        "model": model,

        "features": MODEL_FEATURES,

        "best_parameters": best_params,

        "cv_roc_auc": cv_roc_auc,

        "prediction_threshold": threshold,

        "test_metrics": test_metrics,

        "target_definition": (
            "Customers at or above the 75th percentile "
            "of recency_days are labeled as churned."
        ),

        "model_type": "XGBoost",

        "random_state": RANDOM_STATE,
    }

    with open(
        MODEL_PATH,
        "wb",
    ) as file:

        pickle.dump(
            model_package,
            file,
        )

    print()
    print(
        "XGBoost model saved successfully:"
    )

    print(
        MODEL_PATH
    )

    return model_package


# ============================================================================
# SAVE EVALUATION REPORT
# ============================================================================

def save_report(
    best_params,
    cv_roc_auc,
    threshold,
    test_metrics,
):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = []

    lines.append("=" * 70)
    lines.append(
        "CUSTOMER CHURN PROJECT - XGBOOST EVALUATION"
    )
    lines.append("=" * 70)
    lines.append("")

    lines.append("MODEL")
    lines.append("-" * 70)
    lines.append("Model type                : XGBoost")
    lines.append(
        f"Prediction threshold      : {threshold:.2f}"
    )
    lines.append(
        f"Cross-validation ROC-AUC  : {cv_roc_auc:.4f}"
    )
    lines.append("")

    lines.append("BEST HYPERPARAMETERS")
    lines.append("-" * 70)

    for key, value in best_params.items():

        lines.append(
            f"{key:<25}: {value}"
        )

    lines.append("")

    lines.append("HELD-OUT TEST PERFORMANCE")
    lines.append("-" * 70)

    lines.append(
        f"Accuracy                  : "
        f"{test_metrics['accuracy']:.4f} "
        f"({test_metrics['accuracy'] * 100:.2f}%)"
    )

    lines.append(
        f"Precision                 : "
        f"{test_metrics['precision']:.4f} "
        f"({test_metrics['precision'] * 100:.2f}%)"
    )

    lines.append(
        f"Recall                    : "
        f"{test_metrics['recall']:.4f} "
        f"({test_metrics['recall'] * 100:.2f}%)"
    )

    lines.append(
        f"F1 Score                  : "
        f"{test_metrics['f1']:.4f} "
        f"({test_metrics['f1'] * 100:.2f}%)"
    )

    lines.append(
        f"ROC-AUC                   : "
        f"{test_metrics['roc_auc']:.4f} "
        f"({test_metrics['roc_auc'] * 100:.2f}%)"
    )

    lines.append("")

    lines.append("CONFUSION MATRIX")
    lines.append("-" * 70)

    cm = test_metrics["confusion_matrix"]

    lines.append(
        "                 Predicted"
    )

    lines.append(
        "                 Active  Churned"
    )

    lines.append(
        f"Actual Active    "
        f"{cm[0][0]:>6}  "
        f"{cm[0][1]:>7}"
    )

    lines.append(
        f"Actual Churned   "
        f"{cm[1][0]:>6}  "
        f"{cm[1][1]:>7}"
    )

    lines.append("")
    lines.append("=" * 70)

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "\n".join(lines)
        )

    print()
    print(
        "Evaluation report saved:"
    )

    print(
        OUTPUT_PATH
    )


# ============================================================================
# MAIN
# ============================================================================

def main():

    print("=" * 70)
    print(
        "CUSTOMER CHURN PROJECT - XGBOOST TRAINING"
    )
    print("=" * 70)

    try:

        # ------------------------------------------------------------
        # Load
        # ------------------------------------------------------------

        df = load_data()

        # ------------------------------------------------------------
        # Prepare
        # ------------------------------------------------------------

        X, y = prepare_data(df)

        # ------------------------------------------------------------
        # Split
        # ------------------------------------------------------------

        (
            X_train,
            X_test,
            y_train,
            y_test,
        ) = split_data(X, y)

        # ------------------------------------------------------------
        # Tune
        # ------------------------------------------------------------

        (
            best_model,
            cv_roc_auc,
            best_params,
        ) = tune_xgboost(
            X_train,
            y_train,
        )

        # ------------------------------------------------------------
        # Threshold
        # ------------------------------------------------------------

        (
            optimal_threshold,
            threshold_results,
        ) = optimize_threshold(
            best_model,
            X_train,
            y_train,
        )

        # ------------------------------------------------------------
        # Test
        # ------------------------------------------------------------

        test_metrics = evaluate_model(
            best_model,
            X_test,
            y_test,
            optimal_threshold,
        )

        # ------------------------------------------------------------
        # Save model
        # ------------------------------------------------------------

        save_model(
            model=best_model,
            best_params=best_params,
            cv_roc_auc=cv_roc_auc,
            threshold=optimal_threshold,
            test_metrics=test_metrics,
        )

        # ------------------------------------------------------------
        # Save report
        # ------------------------------------------------------------

        save_report(
            best_params=best_params,
            cv_roc_auc=cv_roc_auc,
            threshold=optimal_threshold,
            test_metrics=test_metrics,
        )

        # ------------------------------------------------------------
        # Final summary
        # ------------------------------------------------------------

        print()
        print("=" * 70)
        print(
            "XGBOOST TRAINING COMPLETE"
        )
        print("=" * 70)

        print()
        print("Final held-out test performance:")

        print(
            f"  Accuracy  : "
            f"{test_metrics['accuracy'] * 100:.2f}%"
        )

        print(
            f"  Precision : "
            f"{test_metrics['precision'] * 100:.2f}%"
        )

        print(
            f"  Recall    : "
            f"{test_metrics['recall'] * 100:.2f}%"
        )

        print(
            f"  F1 Score  : "
            f"{test_metrics['f1'] * 100:.2f}%"
        )

        print(
            f"  ROC-AUC   : "
            f"{test_metrics['roc_auc'] * 100:.2f}%"
        )

        print()
        print(
            f"Optimized threshold: "
            f"{optimal_threshold:.2f}"
        )

        print()
        print(
            "XGBoost model was saved separately."
        )

        print(
            "The existing Random Forest model was NOT overwritten."
        )

        print()
        print("=" * 70)

    except Exception as error:

        print()
        print("=" * 70)
        print(
            "XGBOOST TRAINING FAILED"
        )
        print("=" * 70)

        print()
        print(
            f"Error: {error}"
        )

        raise


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()