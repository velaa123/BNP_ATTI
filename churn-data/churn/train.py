"""
Customer Churn Project - V2 Tuned Model with Threshold Optimization

Purpose:
    Train and tune a Random Forest churn prediction model using
    Feature Engineering V2, optimize the classification threshold
    using out-of-fold validation predictions, and evaluate the
    final model on an untouched test set.

Input:
    ml/data/processed/churn_dataset.csv

Output:
    ml/churn/model/churn_model.pkl

Metrics:
    - Accuracy
    - Precision
    - Recall
    - F1 Score
    - ROC-AUC
    - Cross-validation ROC-AUC
    - Confusion Matrix
    - Feature Importance
    - Optimized Probability Threshold
"""

from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_val_predict,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


# ============================================================
# PATH CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "processed"
    / "churn_dataset.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "ml"
    / "churn"
    / "model"
)

MODEL_FILE = MODEL_DIR / "churn_model.pkl"


# ============================================================
# V2 MODEL FEATURES
# ============================================================

MODEL_FEATURES = [
    # Original behavioral features
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

    # Feature Engineering V2
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
# HELPER FUNCTIONS
# ============================================================

def print_header(title: str) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)


def validate_dataset(df: pd.DataFrame) -> None:
    """Validate required columns and target."""

    required_columns = MODEL_FEATURES + ["churn"]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print("\nERROR: Missing required columns:")

        for column in missing_columns:
            print(f"  - {column}")

        sys.exit(1)

    if df["churn"].nunique() < 2:
        print("\nERROR: Target contains fewer than two classes.")
        sys.exit(1)

    if df["churn"].isna().any():
        print("\nERROR: Target contains missing values.")
        sys.exit(1)


def prepare_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Prepare numeric model features and target."""

    X = df[MODEL_FEATURES].copy()

    y = df["churn"].astype(int).copy()

    for column in MODEL_FEATURES:

        X[column] = pd.to_numeric(
            X[column],
            errors="coerce",
        )

    X = X.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    for column in MODEL_FEATURES:

        if X[column].isna().any():

            median_value = X[column].median()

            if pd.isna(median_value):
                median_value = 0.0

            X[column] = X[column].fillna(
                median_value
            )

    return X, y


def find_best_threshold(
    y_true: pd.Series,
    probabilities: np.ndarray,
) -> tuple[float, pd.DataFrame]:
    """
    Find probability threshold that maximizes F1.

    Threshold selection is performed only on out-of-fold
    predictions from the training data.

    The test set is never used here.
    """

    thresholds = np.arange(
        0.20,
        0.81,
        0.01,
    )

    results = []

    for threshold in thresholds:

        predictions = (
            probabilities >= threshold
        ).astype(int)

        precision = precision_score(
            y_true,
            predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_true,
            predictions,
            zero_division=0,
        )

        f1 = f1_score(
            y_true,
            predictions,
            zero_division=0,
        )

        accuracy = accuracy_score(
            y_true,
            predictions,
        )

        results.append(
            {
                "threshold": round(
                    float(threshold),
                    2,
                ),
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    results_df = pd.DataFrame(results)

    # Maximum F1.
    best_f1 = results_df["f1"].max()

    candidates = results_df[
        results_df["f1"] == best_f1
    ].copy()

    # If multiple thresholds have the same F1,
    # prefer better recall, then precision.
    candidates = candidates.sort_values(
        by=[
            "recall",
            "precision",
            "threshold",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    )

    best_threshold = float(
        candidates.iloc[0]["threshold"]
    )

    return best_threshold, results_df


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print_header(
        "CUSTOMER CHURN PROJECT - "
        "V2 THRESHOLD OPTIMIZED MODEL TRAINING"
    )

    # ========================================================
    # 1. LOAD DATASET
    # ========================================================

    print("\n[1/10] Loading V2 churn dataset...")
    print(f"Input file: {INPUT_FILE}")

    if not INPUT_FILE.exists():

        print("\nERROR: Dataset file not found.")
        print(f"Expected: {INPUT_FILE}")

        sys.exit(1)

    try:

        df = pd.read_csv(
            INPUT_FILE
        )

    except Exception as error:

        print("\nERROR: Failed to load dataset.")
        print(f"Details: {error}")

        sys.exit(1)

    print("Dataset loaded successfully.")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # ========================================================
    # 2. VALIDATE
    # ========================================================

    print("\n[2/10] Validating V2 training data...")

    validate_dataset(df)

    print(
        "All required V2 training columns are available."
    )

    print("Target column is valid.")

    # ========================================================
    # 3. PREPARE FEATURES
    # ========================================================

    print("\n[3/10] Preparing V2 model features...")

    X, y = prepare_features(
        df
    )

    print(
        f"Number of features: "
        f"{len(MODEL_FEATURES)}"
    )

    print("\nFeatures used by V2 model:")

    for feature in MODEL_FEATURES:
        print(f"  - {feature}")

    # ========================================================
    # 4. TARGET DISTRIBUTION
    # ========================================================

    print("\n[4/10] Checking target distribution...")

    class_counts = (
        y.value_counts()
        .sort_index()
    )

    total_samples = len(y)

    for class_value in [0, 1]:

        count = int(
            class_counts.get(
                class_value,
                0,
            )
        )

        percentage = (
            count
            / total_samples
            * 100
        )

        label = (
            "Active"
            if class_value == 0
            else "Churned"
        )

        print(
            f"  {class_value} ({label}): "
            f"{count} "
            f"({percentage:.2f}%)"
        )

    # ========================================================
    # 5. TRAIN / TEST SPLIT
    # ========================================================

    print(
        "\n[5/10] Creating untouched test set..."
    )

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=42,
            stratify=y,
        )
    )

    print(
        f"Training samples: "
        f"{len(X_train)}"
    )

    print(
        f"Testing samples : "
        f"{len(X_test)}"
    )

    print("\nTraining target distribution:")
    print(
        y_train.value_counts()
        .sort_index()
    )

    print("\nTesting target distribution:")
    print(
        y_test.value_counts()
        .sort_index()
    )

    # ========================================================
    # 6. GRID SEARCH
    # ========================================================

    print(
        "\n[6/10] Running V2 Random Forest "
        "hyperparameter tuning..."
    )

    pipeline = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                RandomForestClassifier(
                    random_state=42,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    parameter_grid = {
        "model__n_estimators": [
            200,
            300,
            500,
        ],
        "model__max_depth": [
            5,
            8,
            10,
            12,
        ],
        "model__min_samples_split": [
            5,
            10,
            15,
        ],
        "model__min_samples_leaf": [
            2,
            4,
            6,
        ],
        "model__class_weight": [
            "balanced",
            "balanced_subsample",
        ],
    }

    cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    print(
        "Scoring metric: ROC-AUC"
    )

    print(
        "Cross-validation folds: 5"
    )

    print(
        "Total parameter combinations: 216"
    )

    grid_search = GridSearchCV(
        estimator=pipeline,
        param_grid=parameter_grid,
        scoring="roc_auc",
        cv=cv,
        n_jobs=-1,
        verbose=1,
        refit=True,
    )

    print(
        "\nStarting hyperparameter search..."
    )

    grid_search.fit(
        X_train,
        y_train,
    )

    best_model = (
        grid_search.best_estimator_
    )

    print(
        "\nHyperparameter tuning completed."
    )

    print(
        "\nBest cross-validation "
        "ROC-AUC:"
    )

    print(
        f"{grid_search.best_score_:.4f}"
    )

    print("\nBest parameters:")

    for parameter, value in (
        grid_search.best_params_.items()
    ):

        print(
            f"  {parameter}: {value}"
        )

    # ========================================================
    # 7. THRESHOLD OPTIMIZATION
    # ========================================================

    print(
        "\n[7/10] Optimizing probability "
        "classification threshold..."
    )

    print(
        "Generating out-of-fold "
        "training probabilities..."
    )

    threshold_cv = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=123,
    )

    oof_probabilities = cross_val_predict(
        best_model,
        X_train,
        y_train,
        cv=threshold_cv,
        method="predict_proba",
        n_jobs=-1,
    )[:, 1]

    best_threshold, threshold_results = (
        find_best_threshold(
            y_train,
            oof_probabilities,
        )
    )

    best_row = threshold_results[
        threshold_results["threshold"]
        == best_threshold
    ].iloc[0]

    print(
        "\nOptimal probability threshold:"
    )

    print(
        f"  {best_threshold:.2f}"
    )

    print(
        "\nThreshold optimization "
        "performance:"
    )

    print(
        f"  Accuracy : "
        f"{best_row['accuracy']:.4f}"
    )

    print(
        f"  Precision: "
        f"{best_row['precision']:.4f}"
    )

    print(
        f"  Recall   : "
        f"{best_row['recall']:.4f}"
    )

    print(
        f"  F1 Score : "
        f"{best_row['f1']:.4f}"
    )

    print(
        "\nTest data was NOT used "
        "for threshold selection."
    )

    # ========================================================
    # 8. FINAL TEST EVALUATION
    # ========================================================

    print(
        "\n[8/10] Evaluating V2 final model "
        "on untouched test set..."
    )

    test_probabilities = (
        best_model.predict_proba(
            X_test
        )[:, 1]
    )

    test_predictions = (
        test_probabilities
        >= best_threshold
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        test_predictions,
    )

    precision = precision_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_test,
        test_predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        test_probabilities,
    )

    cm = confusion_matrix(
        y_test,
        test_predictions,
    )

    print("\n")
    print("-" * 70)
    print("V2 FINAL MODEL PERFORMANCE")
    print("-" * 70)

    print(
        f"Cross-validation ROC-AUC : "
        f"{grid_search.best_score_:.4f}"
    )

    print(
        f"Testing Accuracy         : "
        f"{accuracy:.4f}"
    )

    print(
        f"Precision                : "
        f"{precision:.4f}"
    )

    print(
        f"Recall                   : "
        f"{recall:.4f}"
    )

    print(
        f"F1 Score                 : "
        f"{f1:.4f}"
    )

    print(
        f"ROC-AUC                  : "
        f"{roc_auc:.4f}"
    )

    print(
        f"Decision Threshold       : "
        f"{best_threshold:.2f}"
    )

    print("\nConfusion Matrix:")

    print(
        "                 Predicted"
    )

    print(
        "              Active  Churned"
    )

    print(
        f"Actual Active "
        f"{cm[0, 0]:8d}"
        f"{cm[0, 1]:9d}"
    )

    print(
        f"Actual Churned"
        f"{cm[1, 0]:8d}"
        f"{cm[1, 1]:9d}"
    )

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            test_predictions,
            target_names=[
                "Active",
                "Churned",
            ],
            zero_division=0,
        )
    )

    # ========================================================
    # 9. OVERFITTING + FEATURE IMPORTANCE
    # ========================================================

    print(
        "\n[9/10] Analyzing V2 model behavior..."
    )

    train_probabilities = (
        best_model.predict_proba(
            X_train
        )[:, 1]
    )

    train_predictions = (
        train_probabilities
        >= best_threshold
    ).astype(int)

    train_accuracy = accuracy_score(
        y_train,
        train_predictions,
    )

    accuracy_gap = (
        train_accuracy
        - accuracy
    )

    print("\nOverfitting check:")

    print(
        f"Training Accuracy : "
        f"{train_accuracy:.4f}"
    )

    print(
        f"Testing Accuracy  : "
        f"{accuracy:.4f}"
    )

    print(
        f"Accuracy Gap      : "
        f"{accuracy_gap:.4f}"
    )

    if accuracy_gap > 0.15:

        print(
            "WARNING: Significant "
            "overfitting detected."
        )

    elif accuracy_gap > 0.10:

        print(
            "WARNING: Moderate "
            "overfitting detected."
        )

    else:

        print(
            "Overfitting level is acceptable."
        )

    # --------------------------------------------------------
    # Feature importance
    # --------------------------------------------------------

    trained_rf = (
        best_model.named_steps[
            "model"
        ]
    )

    importances = (
        trained_rf.feature_importances_
    )

    importance_df = pd.DataFrame(
        {
            "feature": MODEL_FEATURES,
            "importance": importances,
        }
    ).sort_values(
        by="importance",
        ascending=False,
    )

    print("\nFeature importance:")
    print()
    print("-" * 60)

    print(
        f"{'Feature':35s}"
        f"{'Importance':>15s}"
    )

    print("-" * 60)

    for _, row in (
        importance_df.iterrows()
    ):

        print(
            f"{row['feature']:35s}"
            f"{row['importance']:15.6f}"
        )

    # ========================================================
    # 10. SAVE MODEL
    # ========================================================

    print(
        "\n[10/10] Saving V2 final model..."
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_package = {
        "model": best_model,

        "features": MODEL_FEATURES,

        "best_parameters": (
            grid_search.best_params_
        ),

        "cv_roc_auc": float(
            grid_search.best_score_
        ),

        "test_metrics": {
            "accuracy": float(
                accuracy
            ),
            "precision": float(
                precision
            ),
            "recall": float(
                recall
            ),
            "f1": float(
                f1
            ),
            "roc_auc": float(
                roc_auc
            ),
        },

        "prediction_threshold": float(
            best_threshold
        ),

        "target_definition": (
            "Customers at or above the "
            "75th percentile of recency_days "
            "are labeled as churned."
        ),

        "feature_engineering_version": "V2",

        "number_of_features": len(
            MODEL_FEATURES
        ),

        "threshold_optimization": {
            "method": (
                "5-fold out-of-fold "
                "probability optimization"
            ),
            "objective": "F1",
            "threshold_min": 0.20,
            "threshold_max": 0.80,
            "threshold_step": 0.01,
        },
    }

    try:

        with open(
            MODEL_FILE,
            "wb",
        ) as file:

            pickle.dump(
                model_package,
                file,
            )

    except Exception as error:

        print(
            "\nERROR: Failed to save V2 model."
        )

        print(
            f"Details: {error}"
        )

        sys.exit(1)

    print(
        "V2 final model saved successfully:"
    )

    print(MODEL_FILE)

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)

    print(
        "V2 THRESHOLD OPTIMIZED MODEL "
        "TRAINING COMPLETE"
    )

    print("=" * 70)

    print(
        f"Features         : "
        f"{len(MODEL_FEATURES)}"
    )

    print(
        f"CV ROC-AUC       : "
        f"{grid_search.best_score_:.4f}"
    )

    print(
        f"Test ROC-AUC     : "
        f"{roc_auc:.4f}"
    )

    print(
        f"Recall           : "
        f"{recall:.4f}"
    )

    print(
        f"Precision        : "
        f"{precision:.4f}"
    )

    print(
        f"F1 Score         : "
        f"{f1:.4f}"
    )

    print(
        f"Accuracy         : "
        f"{accuracy:.4f}"
    )

    print(
        f"Optimal Threshold: "
        f"{best_threshold:.2f}"
    )

    print("\nModel ready.")

    print(
        "\nThe saved model package contains:"
    )

    print(
        "  - trained V2 Random Forest"
    )

    print(
        "  - 39 model features"
    )

    print(
        "  - optimized probability threshold"
    )

    print(
        "  - CV ROC-AUC"
    )

    print(
        "  - untouched test metrics"
    )

    print(
        "\nNext step:"
    )

    print(
        "Run: python churn\\predict.py"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()