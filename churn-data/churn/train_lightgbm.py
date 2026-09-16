from pathlib import Path
import pickle
import warnings

import numpy as np
import pandas as pd
import lightgbm as lgb

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
    RandomizedSearchCV,
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

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = (
    MODEL_DIR
    / "lightgbm_churn_model.pkl"
)

EVALUATION_PATH = (
    OUTPUT_DIR
    / "lightgbm_evaluation.txt"
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_STATE = 42
TEST_SIZE = 0.20

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

TARGET_COLUMN = "churn"


# ============================================================
# THRESHOLD OPTIMIZATION
# ============================================================

def find_best_threshold(y_true, probabilities):
    """
    Find threshold that maximizes F1.

    Tie-breaking:
    1. Higher recall
    2. Higher precision
    3. Lower threshold
    """

    best_threshold = 0.50
    best_f1 = -1.0
    best_recall = -1.0
    best_precision = -1.0

    thresholds = np.arange(
        0.20,
        0.801,
        0.01,
    )

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

        if (
            f1 > best_f1
            or (
                np.isclose(f1, best_f1)
                and recall > best_recall
            )
            or (
                np.isclose(f1, best_f1)
                and np.isclose(
                    recall,
                    best_recall,
                )
                and precision > best_precision
            )
        ):
            best_threshold = float(threshold)
            best_f1 = float(f1)
            best_recall = float(recall)
            best_precision = float(precision)

    return best_threshold


# ============================================================
# START
# ============================================================

print("=" * 70)
print("LIGHTGBM CUSTOMER CHURN TRAINING")
print("=" * 70)


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

print(
    f"Dataset: {len(df)} rows"
)

print(
    f"Features: {len(MODEL_FEATURES)}"
)


# ============================================================
# VALIDATION
# ============================================================

missing_features = [
    feature
    for feature in MODEL_FEATURES
    if feature not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing required features: "
        f"{missing_features}"
    )

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' "
        f"not found."
    )


X = df[
    MODEL_FEATURES
].copy()

y = df[
    TARGET_COLUMN
].astype(int)


# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\nTarget distribution:")

target_counts = (
    y.value_counts()
    .sort_index()
)

active_count = int(
    target_counts.get(0, 0)
)

churned_count = int(
    target_counts.get(1, 0)
)

print(
    f"Active:   {active_count} "
    f"({active_count / len(y) * 100:.2f}%)"
)

print(
    f"Churned:  {churned_count} "
    f"({churned_count / len(y) * 100:.2f}%)"
)


# ============================================================
# TRAIN / TEST SPLIT
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


print("\nTrain/Test split:")

print(
    f"Training rows: {len(X_train)}"
)

print(
    f"Testing rows:  {len(X_test)}"
)


# ============================================================
# CLASS IMBALANCE
# ============================================================

scale_pos_weight = (
    (y_train == 0).sum()
    /
    max(
        (y_train == 1).sum(),
        1,
    )
)

print(
    f"\nScale positive weight: "
    f"{scale_pos_weight:.2f}"
)


# ============================================================
# BASE LIGHTGBM MODEL
# ============================================================

base_model = lgb.LGBMClassifier(
    objective="binary",
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbosity=-1,
)


# ============================================================
# HYPERPARAMETER SEARCH
# ============================================================

param_distributions = {

    "n_estimators": [
        200,
        300,
        500,
        700,
        1000,
    ],

    "learning_rate": [
        0.005,
        0.01,
        0.02,
        0.03,
        0.05,
        0.08,
    ],

    "max_depth": [
        2,
        3,
        4,
        5,
        6,
        8,
        -1,
    ],

    "num_leaves": [
        7,
        15,
        23,
        31,
        47,
        63,
    ],

    "min_child_samples": [
        5,
        10,
        15,
        20,
        30,
        50,
    ],

    "subsample": [
        0.7,
        0.8,
        0.9,
        1.0,
    ],

    "colsample_bytree": [
        0.6,
        0.7,
        0.8,
        0.9,
        1.0,
    ],

    "reg_alpha": [
        0.0,
        0.1,
        0.5,
        1.0,
        2.0,
    ],

    "reg_lambda": [
        0.0,
        0.5,
        1.0,
        2.0,
        5.0,
        10.0,
    ],
}


cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE,
)


print("\n" + "=" * 70)
print("LIGHTGBM HYPERPARAMETER SEARCH")
print("=" * 70)

print("\nSearch configuration:")
print("- RandomizedSearchCV")
print("- Candidates: 40")
print("- Cross-validation: 5-fold")
print("- Scoring: ROC-AUC")
print("- Total fits: 200")


search = RandomizedSearchCV(
    estimator=base_model,
    param_distributions=param_distributions,
    n_iter=40,
    scoring="roc_auc",
    cv=cv,
    random_state=RANDOM_STATE,
    n_jobs=-1,
    verbose=1,
    refit=True,
)


search.fit(
    X_train,
    y_train,
)


best_model = search.best_estimator_


# ============================================================
# BEST PARAMETERS
# ============================================================

print("\nBest parameters:")

for key, value in (
    search.best_params_.items()
):
    print(
        f"{key}: {value}"
    )


print(
    f"\nBest CV ROC-AUC: "
    f"{search.best_score_:.4f}"
)


# ============================================================
# OUT-OF-FOLD PROBABILITIES
# ============================================================

print("\n" + "=" * 70)
print("THRESHOLD OPTIMIZATION")
print("=" * 70)

print(
    "\nGenerating out-of-fold probabilities..."
)


oof_probabilities = (
    cross_val_predict(
        best_model,
        X_train,
        y_train,
        cv=cv,
        method="predict_proba",
        n_jobs=1,
    )[:, 1]
)


best_threshold = find_best_threshold(
    y_train,
    oof_probabilities,
)


print(
    f"\nSelected probability threshold: "
    f"{best_threshold:.2f}"
)


# ============================================================
# OOF TRAINING PERFORMANCE
# ============================================================

oof_predictions = (
    oof_probabilities
    >= best_threshold
).astype(int)


oof_accuracy = accuracy_score(
    y_train,
    oof_predictions,
)

oof_precision = precision_score(
    y_train,
    oof_predictions,
    zero_division=0,
)

oof_recall = recall_score(
    y_train,
    oof_predictions,
    zero_division=0,
)

oof_f1 = f1_score(
    y_train,
    oof_predictions,
    zero_division=0,
)


print(
    "\nOut-of-fold training performance:"
)

print(
    f"Accuracy:  {oof_accuracy:.4f}"
)

print(
    f"Precision: {oof_precision:.4f}"
)

print(
    f"Recall:    {oof_recall:.4f}"
)

print(
    f"F1 Score:  {oof_f1:.4f}"
)


# ============================================================
# HELD-OUT TEST PERFORMANCE
# ============================================================

print("\n" + "=" * 70)
print("HELD-OUT TEST PERFORMANCE")
print("=" * 70)


test_probabilities = (
    best_model
    .predict_proba(X_test)[:, 1]
)


test_predictions = (
    test_probabilities
    >= best_threshold
).astype(int)


test_accuracy = accuracy_score(
    y_test,
    test_predictions,
)

test_precision = precision_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_recall = recall_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_f1 = f1_score(
    y_test,
    test_predictions,
    zero_division=0,
)

test_roc_auc = roc_auc_score(
    y_test,
    test_probabilities,
)

test_cm = confusion_matrix(
    y_test,
    test_predictions,
)

test_report = classification_report(
    y_test,
    test_predictions,
    target_names=[
        "Active",
        "Churned",
    ],
    zero_division=0,
)


print(
    f"\nAccuracy:  {test_accuracy:.4f}"
)

print(
    f"Precision: {test_precision:.4f}"
)

print(
    f"Recall:    {test_recall:.4f}"
)

print(
    f"F1 Score:  {test_f1:.4f}"
)

print(
    f"ROC-AUC:   {test_roc_auc:.4f}"
)


print("\nConfusion Matrix:")

print(test_cm)


print("\nClassification Report:")

print(test_report)


# ============================================================
# GENERALIZATION GAP
# ============================================================

train_probabilities = (
    best_model
    .predict_proba(X_train)[:, 1]
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
    -
    test_accuracy
)


print(
    "\nTrain/Test generalization:"
)

print(
    f"Training Accuracy: "
    f"{train_accuracy:.4f}"
)

print(
    f"Testing Accuracy:  "
    f"{test_accuracy:.4f}"
)

print(
    f"Accuracy Gap:      "
    f"{accuracy_gap:.4f}"
)


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

feature_importance = pd.DataFrame(
    {
        "feature": MODEL_FEATURES,
        "importance": (
            best_model
            .feature_importances_
        ),
    }
).sort_values(
    "importance",
    ascending=False,
)


print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)


for _, row in (
    feature_importance
    .head(15)
    .iterrows()
):

    print(
        f"{row['feature']:<32} "
        f"{row['importance']}"
    )


# ============================================================
# MODEL PACKAGE
# ============================================================

model_package = {

    "model": best_model,

    "features": MODEL_FEATURES,

    "best_parameters": (
        search.best_params_
    ),

    "cv_roc_auc": float(
        search.best_score_
    ),

    "prediction_threshold": float(
        best_threshold
    ),

    "test_metrics": {

        "accuracy": float(
            test_accuracy
        ),

        "precision": float(
            test_precision
        ),

        "recall": float(
            test_recall
        ),

        "f1": float(
            test_f1
        ),

        "roc_auc": float(
            test_roc_auc
        ),
    },

    "target_definition": (
        "Customers at or above the "
        "75th percentile of recency_days "
        "are labeled as churned."
    ),

    "threshold_optimization": {

        "method": (
            "Out-of-fold probability "
            "threshold optimization"
        ),

        "objective": "Maximum F1",

        "range": "0.20 to 0.80",
    },
}


# ============================================================
# SAVE MODEL
# ============================================================

with open(
    MODEL_PATH,
    "wb",
) as file:

    pickle.dump(
        model_package,
        file,
    )


# ============================================================
# SAVE EVALUATION REPORT
# ============================================================

report_lines = [

    "LIGHTGBM CUSTOMER CHURN MODEL EVALUATION",

    "=" * 70,

    f"Dataset rows: {len(df)}",

    f"Features: {len(MODEL_FEATURES)}",

    f"Training rows: {len(X_train)}",

    f"Testing rows: {len(X_test)}",

    "",

    "Target Distribution",

    (
        f"Active: {active_count} "
        f"({active_count / len(y) * 100:.2f}%)"
    ),

    (
        f"Churned: {churned_count} "
        f"({churned_count / len(y) * 100:.2f}%)"
    ),

    "",

    "Best Hyperparameters",
]


for key, value in (
    search.best_params_.items()
):

    report_lines.append(
        f"{key}: {value}"
    )


report_lines.extend([

    "",

    (
        f"Best CV ROC-AUC: "
        f"{search.best_score_:.4f}"
    ),

    (
        f"Prediction Threshold: "
        f"{best_threshold:.2f}"
    ),

    "",

    "Out-of-Fold Training Performance",

    (
        f"Accuracy: "
        f"{oof_accuracy:.4f}"
    ),

    (
        f"Precision: "
        f"{oof_precision:.4f}"
    ),

    (
        f"Recall: "
        f"{oof_recall:.4f}"
    ),

    (
        f"F1: "
        f"{oof_f1:.4f}"
    ),

    "",

    "HELD-OUT TEST PERFORMANCE",

    (
        f"Accuracy: "
        f"{test_accuracy:.4f}"
    ),

    (
        f"Precision: "
        f"{test_precision:.4f}"
    ),

    (
        f"Recall: "
        f"{test_recall:.4f}"
    ),

    (
        f"F1: "
        f"{test_f1:.4f}"
    ),

    (
        f"ROC-AUC: "
        f"{test_roc_auc:.4f}"
    ),

    "",

    "Confusion Matrix",

    str(test_cm),

    "",

    "Classification Report",

    test_report,

    (
        f"Training Accuracy: "
        f"{train_accuracy:.4f}"
    ),

    (
        f"Testing Accuracy: "
        f"{test_accuracy:.4f}"
    ),

    (
        f"Accuracy Gap: "
        f"{accuracy_gap:.4f}"
    ),

    "",

    "Target Definition",

    (
        "Customers at or above the "
        "75th percentile of recency_days "
        "are labeled as churned."
    ),

    (
        "recency_days is excluded from "
        "model features to avoid direct "
        "target leakage."
    ),

    "",

    "Top Feature Importances",
])


for _, row in (
    feature_importance
    .head(15)
    .iterrows()
):

    report_lines.append(
        f"{row['feature']}: "
        f"{row['importance']}"
    )


with open(
    EVALUATION_PATH,
    "w",
    encoding="utf-8",
) as file:

    file.write(
        "\n".join(report_lines)
    )


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("LIGHTGBM TRAINING COMPLETED")
print("=" * 70)

print(
    f"\nHeld-out Test Accuracy : "
    f"{test_accuracy * 100:.2f}%"
)

print(
    f"Held-out Test Precision: "
    f"{test_precision * 100:.2f}%"
)

print(
    f"Held-out Test Recall   : "
    f"{test_recall * 100:.2f}%"
)

print(
    f"Held-out Test F1       : "
    f"{test_f1 * 100:.2f}%"
)

print(
    f"Held-out Test ROC-AUC  : "
    f"{test_roc_auc * 100:.2f}%"
)

print(
    f"\nPrediction Threshold: "
    f"{best_threshold:.2f}"
)

print(
    f"\nModel saved to:\n"
    f"{MODEL_PATH}"
)

print(
    f"\nEvaluation saved to:\n"
    f"{EVALUATION_PATH}"
)

print("\n" + "=" * 70)