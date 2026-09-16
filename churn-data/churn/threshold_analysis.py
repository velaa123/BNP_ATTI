from pathlib import Path
import pickle
import warnings

import numpy as np
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_predict,
    train_test_split,
)

warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_PATH = (
    BASE_DIR
    / "ml"
    / "data"
    / "processed"
    / "churn_dataset.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "ml"
    / "churn"
    / "model"
)

OUTPUT_DIR = (
    BASE_DIR
    / "ml"
    / "outputs"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_PATH = (
    OUTPUT_DIR
    / "threshold_analysis.txt"
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20

TARGET_COLUMN = "churn"

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


MODELS = {
    "Random Forest": MODEL_DIR / "churn_model.pkl",
    "XGBoost": MODEL_DIR / "xgboost_churn_model.pkl",
    "CatBoost": MODEL_DIR / "catboost_churn_model.pkl",
    "LightGBM": MODEL_DIR / "lightgbm_churn_model.pkl",
}


# ============================================================
# THRESHOLD RANGE
# ============================================================

THRESHOLDS = np.arange(
    0.20,
    0.801,
    0.01,
)


# ============================================================
# HELPERS
# ============================================================

def load_model_package(path):
    """Load a model package from pickle."""

    if not path.exists():
        raise FileNotFoundError(
            f"Model not found:\n{path}"
        )

    with open(
        path,
        "rb",
    ) as file:
        package = pickle.load(file)

    if isinstance(package, dict):
        if "model" not in package:
            raise ValueError(
                f"Model package does not contain "
                f"'model': {path}"
            )

        return package

    # Fallback for a raw model
    return {
        "model": package,
        "features": MODEL_FEATURES,
    }


def calculate_metrics(
    y_true,
    probabilities,
    threshold,
):
    """Calculate classification metrics."""

    predictions = (
        probabilities >= threshold
    ).astype(int)

    return {
        "accuracy": accuracy_score(
            y_true,
            predictions,
        ),
        "precision": precision_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_true,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_true,
            predictions,
            zero_division=0,
        ),
    }


def find_best_threshold(
    y_true,
    probabilities,
    metric,
):
    """
    Select threshold using OOF training probabilities.

    This threshold is then applied to the untouched
    test set.
    """

    best_threshold = 0.50
    best_score = -1.0

    for threshold in THRESHOLDS:

        metrics = calculate_metrics(
            y_true,
            probabilities,
            threshold,
        )

        score = metrics[metric]

        if score > best_score:
            best_score = score
            best_threshold = float(
                threshold
            )

    return (
        best_threshold,
        best_score,
    )


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 75)
print("MULTI-MODEL THRESHOLD ANALYSIS")
print("=" * 75)

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

missing_features = [
    feature
    for feature in MODEL_FEATURES
    if feature not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing features: {missing_features}"
    )

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Missing target: {TARGET_COLUMN}"
    )


X = df[
    MODEL_FEATURES
].copy()

y = df[
    TARGET_COLUMN
].astype(int)


# ============================================================
# SAME TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = (
    train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
)


print(
    f"\nDataset: {len(df)}"
)

print(
    f"Training: {len(X_train)}"
)

print(
    f"Testing: {len(X_test)}"
)

print(
    "\nThresholds evaluated: "
    "0.20 → 0.80"
)

print(
    "\nIMPORTANT:"
)

print(
    "Thresholds are selected using "
    "out-of-fold TRAINING probabilities."
)

print(
    "The 400-row test set remains untouched "
    "until final evaluation."
)


# ============================================================
# CROSS-VALIDATION
# ============================================================

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE,
)


# ============================================================
# RESULTS
# ============================================================

all_results = []

report_lines = []

report_lines.append(
    "MULTI-MODEL THRESHOLD ANALYSIS"
)

report_lines.append(
    "=" * 75
)

report_lines.append(
    "Thresholds selected using OOF training probabilities."
)

report_lines.append(
    "The held-out test set is used only for final evaluation."
)

report_lines.append("")


# ============================================================
# MODEL LOOP
# ============================================================

for model_name, model_path in MODELS.items():

    print("\n" + "=" * 75)

    print(
        f"{model_name.upper()}"
    )

    print("=" * 75)


    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    package = load_model_package(
        model_path
    )

    model = package["model"]


    saved_threshold = package.get(
        "prediction_threshold",
        None,
    )


    print(
        f"\nSaved threshold: "
        f"{saved_threshold}"
    )


    # --------------------------------------------------------
    # OOF TRAINING PROBABILITIES
    # --------------------------------------------------------

    print(
        "\nGenerating OOF training probabilities..."
    )

    oof_probabilities = (
        cross_val_predict(
            model,
            X_train,
            y_train,
            cv=cv,
            method="predict_proba",
            n_jobs=1,
        )[:, 1]
    )


    # --------------------------------------------------------
    # FIND BEST ACCURACY THRESHOLD
    # --------------------------------------------------------

    accuracy_threshold, accuracy_score_oof = (
        find_best_threshold(
            y_train,
            oof_probabilities,
            "accuracy",
        )
    )


    # --------------------------------------------------------
    # FIND BEST F1 THRESHOLD
    # --------------------------------------------------------

    f1_threshold, f1_score_oof = (
        find_best_threshold(
            y_train,
            oof_probabilities,
            "f1",
        )
    )


    # --------------------------------------------------------
    # TEST PROBABILITIES
    # --------------------------------------------------------

    test_probabilities = (
        model.predict_proba(
            X_test
        )[:, 1]
    )


    test_roc_auc = roc_auc_score(
        y_test,
        test_probabilities,
    )


    # --------------------------------------------------------
    # TEST WITH ACCURACY THRESHOLD
    # --------------------------------------------------------

    accuracy_threshold_metrics = (
        calculate_metrics(
            y_test,
            test_probabilities,
            accuracy_threshold,
        )
    )


    # --------------------------------------------------------
    # TEST WITH F1 THRESHOLD
    # --------------------------------------------------------

    f1_threshold_metrics = (
        calculate_metrics(
            y_test,
            test_probabilities,
            f1_threshold,
        )
    )


    # --------------------------------------------------------
    # TEST WITH SAVED THRESHOLD
    # --------------------------------------------------------

    if saved_threshold is not None:

        saved_threshold_metrics = (
            calculate_metrics(
                y_test,
                test_probabilities,
                float(saved_threshold),
            )
        )

    else:

        saved_threshold_metrics = None


    # --------------------------------------------------------
    # DISPLAY
    # --------------------------------------------------------

    print(
        f"\nBest OOF Accuracy Threshold: "
        f"{accuracy_threshold:.2f}"
    )

    print(
        f"OOF Accuracy: "
        f"{accuracy_score_oof:.4f}"
    )

    print(
        f"\nBest OOF F1 Threshold: "
        f"{f1_threshold:.2f}"
    )

    print(
        f"OOF F1: "
        f"{f1_score_oof:.4f}"
    )

    print(
        f"\nROC-AUC on untouched test: "
        f"{test_roc_auc:.4f}"
    )


    print(
        "\nTEST PERFORMANCE — ACCURACY-OPTIMIZED THRESHOLD"
    )

    print(
        f"Threshold: {accuracy_threshold:.2f}"
    )

    print(
        f"Accuracy:  "
        f"{accuracy_threshold_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{accuracy_threshold_metrics['precision']:.4f}"
    )

    print(
        f"Recall:    "
        f"{accuracy_threshold_metrics['recall']:.4f}"
    )

    print(
        f"F1:        "
        f"{accuracy_threshold_metrics['f1']:.4f}"
    )


    print(
        "\nTEST PERFORMANCE — F1-OPTIMIZED THRESHOLD"
    )

    print(
        f"Threshold: {f1_threshold:.2f}"
    )

    print(
        f"Accuracy:  "
        f"{f1_threshold_metrics['accuracy']:.4f}"
    )

    print(
        f"Precision: "
        f"{f1_threshold_metrics['precision']:.4f}"
    )

    print(
        f"Recall:    "
        f"{f1_threshold_metrics['recall']:.4f}"
    )

    print(
        f"F1:        "
        f"{f1_threshold_metrics['f1']:.4f}"
    )


    if saved_threshold_metrics:

        print(
            "\nTEST PERFORMANCE — CURRENT SAVED THRESHOLD"
        )

        print(
            f"Threshold: "
            f"{float(saved_threshold):.2f}"
        )

        print(
            f"Accuracy:  "
            f"{saved_threshold_metrics['accuracy']:.4f}"
        )

        print(
            f"Precision: "
            f"{saved_threshold_metrics['precision']:.4f}"
        )

        print(
            f"Recall:    "
            f"{saved_threshold_metrics['recall']:.4f}"
        )

        print(
            f"F1:        "
            f"{saved_threshold_metrics['f1']:.4f}"
        )


    # --------------------------------------------------------
    # STORE RESULTS
    # --------------------------------------------------------

    result = {
        "model": model_name,

        "saved_threshold": (
            float(saved_threshold)
            if saved_threshold is not None
            else np.nan
        ),

        "accuracy_threshold": (
            accuracy_threshold
        ),

        "f1_threshold": (
            f1_threshold
        ),

        "test_roc_auc": (
            test_roc_auc
        ),

        "accuracy_threshold_accuracy": (
            accuracy_threshold_metrics[
                "accuracy"
            ]
        ),

        "accuracy_threshold_precision": (
            accuracy_threshold_metrics[
                "precision"
            ]
        ),

        "accuracy_threshold_recall": (
            accuracy_threshold_metrics[
                "recall"
            ]
        ),

        "accuracy_threshold_f1": (
            accuracy_threshold_metrics[
                "f1"
            ]
        ),

        "f1_threshold_accuracy": (
            f1_threshold_metrics[
                "accuracy"
            ]
        ),

        "f1_threshold_precision": (
            f1_threshold_metrics[
                "precision"
            ]
        ),

        "f1_threshold_recall": (
            f1_threshold_metrics[
                "recall"
            ]
        ),

        "f1_threshold_f1": (
            f1_threshold_metrics[
                "f1"
            ]
        ),
    }


    if saved_threshold_metrics:

        result.update(
            {
                "saved_accuracy": (
                    saved_threshold_metrics[
                        "accuracy"
                    ]
                ),

                "saved_precision": (
                    saved_threshold_metrics[
                        "precision"
                    ]
                ),

                "saved_recall": (
                    saved_threshold_metrics[
                        "recall"
                    ]
                ),

                "saved_f1": (
                    saved_threshold_metrics[
                        "f1"
                    ]
                ),
            }
        )


    all_results.append(
        result
    )


    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report_lines.extend(
        [
            "",
            "=" * 75,
            model_name,
            "=" * 75,
            "",
            (
                f"Saved threshold: "
                f"{saved_threshold}"
            ),
            (
                f"Best OOF accuracy threshold: "
                f"{accuracy_threshold:.2f}"
            ),
            (
                f"Best OOF F1 threshold: "
                f"{f1_threshold:.2f}"
            ),
            (
                f"Test ROC-AUC: "
                f"{test_roc_auc:.4f}"
            ),
            "",
            "TEST — ACCURACY-OPTIMIZED",
            (
                f"Threshold: "
                f"{accuracy_threshold:.2f}"
            ),
            (
                f"Accuracy: "
                f"{accuracy_threshold_metrics['accuracy']:.4f}"
            ),
            (
                f"Precision: "
                f"{accuracy_threshold_metrics['precision']:.4f}"
            ),
            (
                f"Recall: "
                f"{accuracy_threshold_metrics['recall']:.4f}"
            ),
            (
                f"F1: "
                f"{accuracy_threshold_metrics['f1']:.4f}"
            ),
            "",
            "TEST — F1-OPTIMIZED",
            (
                f"Threshold: "
                f"{f1_threshold:.2f}"
            ),
            (
                f"Accuracy: "
                f"{f1_threshold_metrics['accuracy']:.4f}"
            ),
            (
                f"Precision: "
                f"{f1_threshold_metrics['precision']:.4f}"
            ),
            (
                f"Recall: "
                f"{f1_threshold_metrics['recall']:.4f}"
            ),
            (
                f"F1: "
                f"{f1_threshold_metrics['f1']:.4f}"
            ),
        ]
    )


# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(
    all_results
)


# ============================================================
# SAVE CSV
# ============================================================

csv_path = (
    OUTPUT_DIR
    / "threshold_analysis.csv"
)

results_df.to_csv(
    csv_path,
    index=False,
)


# ============================================================
# FINAL COMPARISON
# ============================================================

print("\n" + "=" * 75)
print("FINAL THRESHOLD COMPARISON")
print("=" * 75)

display_columns = [
    "model",
    "saved_threshold",
    "accuracy_threshold",
    "accuracy_threshold_accuracy",
    "accuracy_threshold_precision",
    "accuracy_threshold_recall",
    "accuracy_threshold_f1",
    "f1_threshold",
    "f1_threshold_accuracy",
    "f1_threshold_f1",
    "test_roc_auc",
]


print(
    results_df[
        display_columns
    ].to_string(
        index=False
    )
)


# ============================================================
# ADD SUMMARY TO REPORT
# ============================================================

report_lines.extend(
    [
        "",
        "=" * 75,
        "FINAL COMPARISON",
        "=" * 75,
        "",
        results_df[
            display_columns
        ].to_string(
            index=False
        ),
        "",
        "IMPORTANT:",
        (
            "Thresholds were selected using "
            "out-of-fold training probabilities."
        ),
        (
            "The held-out test set was not used "
            "to select thresholds."
        ),
    ]
)


# ============================================================
# SAVE REPORT
# ============================================================

with open(
    REPORT_PATH,
    "w",
    encoding="utf-8",
) as file:

    file.write(
        "\n".join(report_lines)
    )


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 75)
print("THRESHOLD ANALYSIS COMPLETED")
print("=" * 75)

print(
    f"\nCSV saved to:\n{csv_path}"
)

print(
    f"\nReport saved to:\n{REPORT_PATH}"
)

print(
    "\nNext step: Feature Engineering V2"
)

print("=" * 75)