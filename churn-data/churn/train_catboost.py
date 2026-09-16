from pathlib import Path
import pickle
import warnings

import numpy as np
import pandas as pd

from catboost import CatBoostClassifier
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

DATA_PATH = BASE_DIR / "ml" / "data" / "processed" / "churn_dataset.csv"
MODEL_DIR = BASE_DIR / "ml" / "churn" / "model"
OUTPUT_DIR = BASE_DIR / "ml" / "outputs"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "catboost_churn_model.pkl"
EVALUATION_PATH = OUTPUT_DIR / "catboost_evaluation.txt"


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
# HELPER
# ============================================================

def find_best_threshold(y_true, probabilities):
    """
    Find the probability threshold that maximizes F1.

    Tie-breaking:
    1. Higher recall
    2. Higher precision
    3. Lower threshold
    """

    best_threshold = 0.50
    best_f1 = -1.0
    best_recall = -1.0
    best_precision = -1.0

    thresholds = np.arange(0.20, 0.801, 0.01)

    for threshold in thresholds:
        predictions = (probabilities >= threshold).astype(int)

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
                and np.isclose(recall, best_recall)
                and precision > best_precision
            )
        ):
            best_threshold = float(threshold)
            best_f1 = float(f1)
            best_recall = float(recall)
            best_precision = float(precision)

    return best_threshold


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("CATBOOST CUSTOMER CHURN TRAINING")
print("=" * 70)

print("\nLoading dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Dataset: {len(df)} rows")
print(f"Features: {len(MODEL_FEATURES)}")


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
        f"Missing required features: {missing_features}"
    )

if TARGET_COLUMN not in df.columns:
    raise ValueError(
        f"Target column '{TARGET_COLUMN}' not found."
    )


X = df[MODEL_FEATURES].copy()
y = df[TARGET_COLUMN].astype(int)


print("\nTarget distribution:")

target_counts = y.value_counts().sort_index()

active_count = int(target_counts.get(0, 0))
churned_count = int(target_counts.get(1, 0))

print(f"Active:   {active_count} ({active_count / len(y) * 100:.2f}%)")
print(f"Churned:  {churned_count} ({churned_count / len(y) * 100:.2f}%)")


# ============================================================
# TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=TEST_SIZE,
    stratify=y,
    random_state=RANDOM_STATE,
)

print("\nTrain/Test split:")
print(f"Training rows: {len(X_train)}")
print(f"Testing rows:  {len(X_test)}")


# ============================================================
# CATBOOST BASE CONFIGURATION
# ============================================================

scale_pos_weight = (
    (y_train == 0).sum() /
    max((y_train == 1).sum(), 1)
)

print(f"\nScale positive weight: {scale_pos_weight:.2f}")


base_model = CatBoostClassifier(
    loss_function="Logloss",
    eval_metric="AUC",
    random_seed=RANDOM_STATE,
    verbose=False,
    thread_count=-1,
    allow_writing_files=False,
)


# ============================================================
# HYPERPARAMETER SEARCH
# ============================================================

param_distributions = {
    "iterations": [
        300,
        500,
        700,
        1000,
    ],
    "depth": [
        4,
        5,
        6,
        7,
        8,
    ],
    "learning_rate": [
        0.01,
        0.02,
        0.03,
        0.05,
        0.08,
    ],
    "l2_leaf_reg": [
        1,
        3,
        5,
        7,
        10,
    ],
    "random_strength": [
        0.0,
        0.5,
        1.0,
        2.0,
    ],
    "bagging_temperature": [
        0.0,
        0.5,
        1.0,
        2.0,
    ],
    "border_count": [
        32,
        64,
        128,
        254,
    ],
}


cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=RANDOM_STATE,
)


print("\n" + "=" * 70)
print("CATBOOST HYPERPARAMETER SEARCH")
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

print("\nBest parameters:")

for key, value in search.best_params_.items():
    print(f"{key}: {value}")

print(
    f"\nBest CV ROC-AUC: "
    f"{search.best_score_:.4f}"
)


# ============================================================
# OUT-OF-FOLD THRESHOLD OPTIMIZATION
# ============================================================

print("\n" + "=" * 70)
print("THRESHOLD OPTIMIZATION")
print("=" * 70)

print("\nGenerating out-of-fold probabilities...")

oof_probabilities = cross_val_predict(
    best_model,
    X_train,
    y_train,
    cv=cv,
    method="predict_proba",
    n_jobs=1,
)[:, 1]


best_threshold = find_best_threshold(
    y_train,
    oof_probabilities,
)

print(
    f"\nSelected probability threshold: "
    f"{best_threshold:.2f}"
)


# ============================================================
# TRAINING PERFORMANCE AT OPTIMIZED THRESHOLD
# ============================================================

oof_predictions = (
    oof_probabilities >= best_threshold
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

print("\nOut-of-fold training performance:")
print(f"Accuracy:  {oof_accuracy:.4f}")
print(f"Precision: {oof_precision:.4f}")
print(f"Recall:    {oof_recall:.4f}")
print(f"F1 Score:  {oof_f1:.4f}")


# ============================================================
# FINAL HELD-OUT TEST
# ============================================================

print("\n" + "=" * 70)
print("HELD-OUT TEST PERFORMANCE")
print("=" * 70)

test_probabilities = best_model.predict_proba(
    X_test
)[:, 1]

test_predictions = (
    test_probabilities >= best_threshold
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


print(f"\nAccuracy:  {test_accuracy:.4f}")
print(f"Precision: {test_precision:.4f}")
print(f"Recall:    {test_recall:.4f}")
print(f"F1 Score:  {test_f1:.4f}")
print(f"ROC-AUC:   {test_roc_auc:.4f}")

print("\nConfusion Matrix:")
print(test_cm)

print("\nClassification Report:")
print(test_report)


# ============================================================
# TRAIN / TEST GAP
# ============================================================

train_probabilities = best_model.predict_proba(
    X_train
)[:, 1]

train_predictions = (
    train_probabilities >= best_threshold
).astype(int)

train_accuracy = accuracy_score(
    y_train,
    train_predictions,
)

accuracy_gap = train_accuracy - test_accuracy


print("\nTrain/Test generalization:")
print(f"Training Accuracy: {train_accuracy:.4f}")
print(f"Testing Accuracy:  {test_accuracy:.4f}")
print(f"Accuracy Gap:      {accuracy_gap:.4f}")


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

feature_importance = pd.DataFrame(
    {
        "feature": MODEL_FEATURES,
        "importance": best_model.get_feature_importance(),
    }
).sort_values(
    "importance",
    ascending=False,
)


print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)

for _, row in feature_importance.head(15).iterrows():
    print(
        f"{row['feature']:<32} "
        f"{row['importance']:.6f}"
    )


# ============================================================
# MODEL PACKAGE
# ============================================================

model_package = {
    "model": best_model,
    "features": MODEL_FEATURES,
    "best_parameters": search.best_params_,
    "cv_roc_auc": float(search.best_score_),
    "prediction_threshold": float(best_threshold),
    "test_metrics": {
        "accuracy": float(test_accuracy),
        "precision": float(test_precision),
        "recall": float(test_recall),
        "f1": float(test_f1),
        "roc_auc": float(test_roc_auc),
    },
    "target_definition": (
        "Customers at or above the 75th percentile "
        "of recency_days are labeled as churned."
    ),
    "threshold_optimization": {
        "method": "Out-of-fold probability threshold optimization",
        "objective": "Maximum F1",
        "range": "0.20 to 0.80",
    },
}


# ============================================================
# SAVE MODEL
# ============================================================

with open(MODEL_PATH, "wb") as file:
    pickle.dump(
        model_package,
        file,
    )


# ============================================================
# SAVE EVALUATION REPORT
# ============================================================

report_lines = []

report_lines.append(
    "CATBOOST CUSTOMER CHURN MODEL EVALUATION"
)

report_lines.append(
    "=" * 70
)

report_lines.append(
    f"Dataset rows: {len(df)}"
)

report_lines.append(
    f"Features: {len(MODEL_FEATURES)}"
)

report_lines.append(
    f"Training rows: {len(X_train)}"
)

report_lines.append(
    f"Testing rows: {len(X_test)}"
)

report_lines.append("")

report_lines.append(
    "Target Distribution"
)

report_lines.append(
    f"Active: {active_count} "
    f"({active_count / len(y) * 100:.2f}%)"
)

report_lines.append(
    f"Churned: {churned_count} "
    f"({churned_count / len(y) * 100:.2f}%)"
)

report_lines.append("")

report_lines.append(
    "Best Hyperparameters"
)

for key, value in search.best_params_.items():
    report_lines.append(
        f"{key}: {value}"
    )

report_lines.append("")

report_lines.append(
    f"Best CV ROC-AUC: {search.best_score_:.4f}"
)

report_lines.append(
    f"Prediction Threshold: {best_threshold:.2f}"
)

report_lines.append("")

report_lines.append(
    "Out-of-Fold Training Performance"
)

report_lines.append(
    f"Accuracy: {oof_accuracy:.4f}"
)

report_lines.append(
    f"Precision: {oof_precision:.4f}"
)

report_lines.append(
    f"Recall: {oof_recall:.4f}"
)

report_lines.append(
    f"F1: {oof_f1:.4f}"
)

report_lines.append("")

report_lines.append(
    "HELD-OUT TEST PERFORMANCE"
)

report_lines.append(
    f"Accuracy: {test_accuracy:.4f}"
)

report_lines.append(
    f"Precision: {test_precision:.4f}"
)

report_lines.append(
    f"Recall: {test_recall:.4f}"
)

report_lines.append(
    f"F1: {test_f1:.4f}"
)

report_lines.append(
    f"ROC-AUC: {test_roc_auc:.4f}"
)

report_lines.append("")

report_lines.append(
    "Confusion Matrix"
)

report_lines.append(
    str(test_cm)
)

report_lines.append("")

report_lines.append(
    "Classification Report"
)

report_lines.append(
    test_report
)

report_lines.append(
    f"Training Accuracy: {train_accuracy:.4f}"
)

report_lines.append(
    f"Testing Accuracy: {test_accuracy:.4f}"
)

report_lines.append(
    f"Accuracy Gap: {accuracy_gap:.4f}"
)

report_lines.append("")

report_lines.append(
    "Target Definition"
)

report_lines.append(
    "Customers at or above the 75th percentile "
    "of recency_days are labeled as churned."
)

report_lines.append(
    "recency_days is excluded from model features "
    "to avoid direct target leakage."
)

report_lines.append("")

report_lines.append(
    "Top Feature Importances"
)

for _, row in feature_importance.head(15).iterrows():
    report_lines.append(
        f"{row['feature']}: "
        f"{row['importance']:.6f}"
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
print("CATBOOST TRAINING COMPLETED")
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
    f"\nModel saved to:"
    f"\n{MODEL_PATH}"
)

print(
    f"\nEvaluation saved to:"
    f"\n{EVALUATION_PATH}"
)

print("\n" + "=" * 70)