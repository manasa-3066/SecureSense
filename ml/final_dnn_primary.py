# ============================================================
# SECURESENSE
# FINAL PRIMARY DNN TRAINING
#
# Purpose:
#   Primary supervised-learning evaluation of SecureSense DNN
#
# Method:
#   - Cleaned CICIDS2017 binary dataset
#   - 69 frozen model features
#   - Stratified 80/10/10 train/validation/test split
#   - StandardScaler fitted ONLY on training data
#   - Same DNN architecture used in the validated experiment
#   - Threshold selected ONLY on validation set
#   - Final test evaluated ONCE after everything is frozen
#
# IMPORTANT:
#   This script does NOT use the previous source-disjoint
#   DDoS-only test split.
#   That experiment remains as a separate generalization study.
# ============================================================

import os
import sys
import time
import json
import pickle
import random
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    classification_report,
)

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# ============================================================
# 1. REPRODUCIBILITY
# ============================================================

SEED = 42

os.environ["PYTHONHASHSEED"] = str(SEED)

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

try:
    tf.config.experimental.enable_op_determinism()
except Exception:
    pass


# ============================================================
# 2. PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    BASE_DIR
    / "data"
    / "cleaned"
    / "securesense_final_binary.parquet"
)

FEATURE_PATH = (
    BASE_DIR
    / "models"
    / "final_feature_names.pkl"
)

MODEL_DIR = BASE_DIR / "models"
RESULT_DIR = BASE_DIR / "results" / "final_primary_dnn"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3. FINAL ARTIFACT NAMES
# ============================================================

FINAL_MODEL_PATH = MODEL_DIR / "primary_dnn.keras"
FINAL_SCALER_PATH = MODEL_DIR / "primary_dnn_scaler.pkl"
FINAL_THRESHOLD_PATH = MODEL_DIR / "primary_dnn_threshold.pkl"

METRICS_PATH = RESULT_DIR / "primary_dnn_test_metrics.csv"
CONFUSION_PATH = RESULT_DIR / "primary_dnn_confusion_matrix.csv"
REPORT_PATH = RESULT_DIR / "primary_dnn_classification_report.csv"
HISTORY_PATH = RESULT_DIR / "primary_dnn_training_history.csv"
CONFIG_PATH = RESULT_DIR / "primary_dnn_configuration.json"
SPLIT_PATH = RESULT_DIR / "primary_dnn_split_summary.csv"


# ============================================================
# 4. HEADER
# ============================================================

print("=" * 80)
print("SECURESENSE - FINAL PRIMARY DNN TRAINING")
print("=" * 80)

print("\nProject directory:")
print(BASE_DIR)

print("\nTensorFlow version:")
print(tf.__version__)

print("\nRandom seed:")
print(SEED)


# ============================================================
# 5. CHECK REQUIRED FILES
# ============================================================

print("\n" + "=" * 80)
print("CHECKING REQUIRED FILES")
print("=" * 80)

if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found:\n{DATA_PATH}"
    )

if not FEATURE_PATH.exists():
    raise FileNotFoundError(
        f"Frozen feature list not found:\n{FEATURE_PATH}"
    )

print("Dataset : FOUND")
print("Features: FOUND")


# ============================================================
# 6. LOAD DATASET
# ============================================================

print("\n" + "=" * 80)
print("LOADING DATASET")
print("=" * 80)

print("\nLoading:")
print(DATA_PATH)

df = pd.read_parquet(DATA_PATH)

print("\nDataset shape:")
print(df.shape)

if "Label" not in df.columns:
    raise ValueError("Label column not found.")

if "BinaryLabel" not in df.columns:
    raise ValueError("BinaryLabel column not found.")


# ============================================================
# 7. LOAD FROZEN 69 FEATURES
# ============================================================

print("\n" + "=" * 80)
print("LOADING FROZEN FEATURE LIST")
print("=" * 80)

with open(FEATURE_PATH, "rb") as f:
    frozen_features = pickle.load(f)

frozen_features = list(frozen_features)

print("\nFrozen feature count:")
print(len(frozen_features))

if len(frozen_features) != 69:
    raise ValueError(
        f"Expected exactly 69 features, found {len(frozen_features)}"
    )

missing_features = [
    feature for feature in frozen_features
    if feature not in df.columns
]

if missing_features:
    raise ValueError(
        f"Missing frozen features:\n{missing_features}"
    )

print("Feature validation: PASS")


# ============================================================
# 8. VERIFY BINARY LABEL
# ============================================================

print("\n" + "=" * 80)
print("VERIFYING BINARY LABEL")
print("=" * 80)

binary_labels = (
    df["BinaryLabel"]
    .astype(str)
    .str.strip()
    .str.upper()
)

print("Unique BinaryLabel values:")
print(sorted(binary_labels.unique()))

valid_labels = {"BENIGN", "ATTACK"}

if not set(binary_labels.unique()).issubset(valid_labels):
    raise ValueError(
        f"Unexpected BinaryLabel values found: "
        f"{sorted(binary_labels.unique())}"
    )

y = np.where(
    binary_labels == "ATTACK",
    1,
    0
).astype(np.int32)

unique_labels = np.unique(y)

print("\nConverted numeric labels:")
print(unique_labels)

if not np.array_equal(
    unique_labels,
    np.array([0, 1])
):
    raise ValueError(
        f"Binary label conversion failed. "
        f"Found: {unique_labels}"
    )

print("Binary label conversion: PASS")

benign_count = int((y == 0).sum())
attack_count = int((y == 1).sum())

print("\nTotal samples :", len(y))
print("Benign        :", f"{benign_count:,}")
print("Attack        :", f"{attack_count:,}")

print(
    "Benign %      :",
    f"{benign_count / len(y) * 100:.4f}%"
)

print(
    "Attack %      :",
    f"{attack_count / len(y) * 100:.4f}%"
)

print("Binary label validation: PASS")


# ============================================================
# 9. EXTRACT FEATURES
# ============================================================

print("\n" + "=" * 80)
print("PREPARING FEATURE MATRIX")
print("=" * 80)

X = df[frozen_features].to_numpy(dtype=np.float32)

print("Feature matrix shape:")
print(X.shape)

if X.shape[1] != 69:
    raise ValueError(
        f"Expected 69 features, found {X.shape[1]}"
    )

if not np.isfinite(X).all():
    raise ValueError(
        "Feature matrix contains NaN or infinite values."
    )

print("NaN / Inf check: PASS")


# ============================================================
# 10. DELETE LARGE ORIGINAL DATAFRAME
# ============================================================

# We no longer need the original dataframe after extracting
# the required features and labels.

del df


# ============================================================
# 11. STRATIFIED 80/10/10 SPLIT
# ============================================================

print("\n" + "=" * 80)
print("CREATING STRATIFIED 80/10/10 SPLIT")
print("=" * 80)

# First split:
# 90% temporary training+validation
# 10% final test

X_temp, X_test, y_temp, y_test = train_test_split(
    X,
    y,
    test_size=0.10,
    stratify=y,
    random_state=SEED,
)

# Second split:
# 90% of temporary = 81% overall
# 10% of temporary = 9% overall
#
# This gives approximately:
# TRAIN = 81%
# VALIDATION = 9%
# TEST = 10%
#
# We use this instead of two equal splits because the
# dataset is very large and we want a substantial test set.

X_train, X_val, y_train, y_val = train_test_split(
    X_temp,
    y_temp,
    test_size=0.10,
    stratify=y_temp,
    random_state=SEED,
)

del X_temp
del y_temp
del X

print("\nSplit sizes:")
print("Train      :", X_train.shape)
print("Validation :", X_val.shape)
print("Test       :", X_test.shape)


# ============================================================
# 12. SPLIT LABEL DISTRIBUTION
# ============================================================

def print_distribution(name, labels):

    benign = int((labels == 0).sum())
    attack = int((labels == 1).sum())
    total = len(labels)

    print(f"\n{name}")
    print("-" * 50)
    print("Total  :", f"{total:,}")
    print("Benign :", f"{benign:,}", f"({benign / total * 100:.4f}%)")
    print("Attack :", f"{attack:,}", f"({attack / total * 100:.4f}%)")


print_distribution("TRAIN", y_train)
print_distribution("VALIDATION", y_val)
print_distribution("TEST", y_test)


# ============================================================
# 13. CHECK LABEL DISTRIBUTION
# ============================================================

for split_name, labels in [
    ("TRAIN", y_train),
    ("VALIDATION", y_val),
    ("TEST", y_test),
]:

    if len(np.unique(labels)) != 2:
        raise ValueError(
            f"{split_name} does not contain both classes."
        )

print("\nStratification validation: PASS")


# ============================================================
# 14. SAVE SPLIT SUMMARY
# ============================================================

split_rows = []

for split_name, labels in [
    ("TRAIN", y_train),
    ("VALIDATION", y_val),
    ("TEST", y_test),
]:

    benign = int((labels == 0).sum())
    attack = int((labels == 1).sum())
    total = len(labels)

    split_rows.append({
        "Split": split_name,
        "Samples": total,
        "Benign": benign,
        "Attack": attack,
        "Benign_Percent": benign / total,
        "Attack_Percent": attack / total,
    })

split_df = pd.DataFrame(split_rows)

split_df.to_csv(
    SPLIT_PATH,
    index=False
)


# ============================================================
# 15. FIT STANDARD SCALER ONLY ON TRAINING DATA
# ============================================================

print("\n" + "=" * 80)
print("FITTING STANDARD SCALER")
print("=" * 80)

scaler = StandardScaler()

scaler.fit(X_train)

print(
    "Scaler fitted samples:",
    scaler.n_samples_seen_
)

if int(scaler.n_samples_seen_) != len(X_train):
    raise ValueError(
        "Scaler sample count does not match training set."
    )

print("Scaler provenance: PASS")


# ============================================================
# 16. TRANSFORM ALL SPLITS
# ============================================================

print("\nTransforming training data...")

X_train_scaled = scaler.transform(
    X_train
).astype(np.float32)

print("Transforming validation data...")

X_val_scaled = scaler.transform(
    X_val
).astype(np.float32)

print("Transforming test data...")

X_test_scaled = scaler.transform(
    X_test
).astype(np.float32)


if not np.isfinite(X_train_scaled).all():
    raise ValueError("Training scaled data contains NaN/Inf.")

if not np.isfinite(X_val_scaled).all():
    raise ValueError("Validation scaled data contains NaN/Inf.")

if not np.isfinite(X_test_scaled).all():
    raise ValueError("Test scaled data contains NaN/Inf.")

print("Scaled data validation: PASS")


# ============================================================
# 17. DELETE UNSCALED TRAIN/VAL DATA
# ============================================================

del X_train
del X_val


# ============================================================
# 18. BUILD FINAL DNN
# ============================================================

print("\n" + "=" * 80)
print("BUILDING DNN")
print("=" * 80)

model = keras.Sequential(
    [
        layers.Input(shape=(69,)),

        layers.Dense(
            256,
            activation="relu"
        ),
        layers.BatchNormalization(),
        layers.Dropout(0.30),

        layers.Dense(
            128,
            activation="relu"
        ),
        layers.BatchNormalization(),
        layers.Dropout(0.25),

        layers.Dense(
            64,
            activation="relu"
        ),
        layers.BatchNormalization(),
        layers.Dropout(0.20),

        layers.Dense(
            32,
            activation="relu"
        ),

        layers.Dense(
            1,
            activation="sigmoid"
        ),
    ],
    name="SecureSense_DNN",
)


# ============================================================
# 19. COMPILE
# ============================================================

model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        keras.metrics.BinaryAccuracy(
            name="accuracy"
        ),
        keras.metrics.Precision(
            name="precision"
        ),
        keras.metrics.Recall(
            name="recall"
        ),
        keras.metrics.AUC(
            name="roc_auc",
            curve="ROC"
        ),
        keras.metrics.AUC(
            name="pr_auc",
            curve="PR"
        ),
    ],
)

print("\nDNN summary:")
model.summary()


# ============================================================
# 20. TRAINING CALLBACKS
# ============================================================

early_stopping = keras.callbacks.EarlyStopping(
    monitor="val_loss",
    patience=3,
    restore_best_weights=True,
    verbose=1,
)

reduce_lr = keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=1,
    min_lr=1e-6,
    verbose=1,
)


# ============================================================
# 21. TRAIN
# ============================================================

print("\n" + "=" * 80)
print("STARTING DNN TRAINING")
print("=" * 80)

print("\nTraining samples:")
print(f"{len(y_train) if 'y_train' in locals() else 'N/A'}")

print("Validation samples:")
print(f"{len(y_val) if 'y_val' in locals() else 'N/A'}")

print("\nBatch size : 4096")
print("Max epochs : 15")

training_start = time.perf_counter()

history = model.fit(
    X_train_scaled,
    y_train,
    validation_data=(
        X_val_scaled,
        y_val,
    ),
    epochs=15,
    batch_size=4096,
    callbacks=[
        early_stopping,
        reduce_lr,
    ],
    verbose=1,
)

training_end = time.perf_counter()

training_time = (
    training_end - training_start
)

print("\nTraining complete.")

print(
    "Training time:",
    f"{training_time:.2f} seconds"
)


# ============================================================
# 22. SAVE TRAINING HISTORY
# ============================================================

history_df = pd.DataFrame(
    history.history
)

history_df.insert(
    0,
    "epoch",
    np.arange(1, len(history_df) + 1)
)

history_df.to_csv(
    HISTORY_PATH,
    index=False
)


# ============================================================
# 23. VALIDATION PROBABILITIES
# ============================================================

print("\n" + "=" * 80)
print("VALIDATION THRESHOLD SELECTION")
print("=" * 80)

val_probabilities = model.predict(
    X_val_scaled,
    batch_size=8192,
    verbose=1
).reshape(-1)

if not np.isfinite(val_probabilities).all():
    raise ValueError(
        "Validation probabilities contain NaN/Inf."
    )

if (
    np.min(val_probabilities) < 0
    or np.max(val_probabilities) > 1
):
    raise ValueError(
        "Validation probabilities outside [0,1]."
    )

print("Probability validation: PASS")


# ============================================================
# 24. SEARCH VALIDATION THRESHOLD
# ============================================================

thresholds = np.arange(
    0.05,
    0.951,
    0.01
)

threshold_results = []

for threshold in thresholds:

    val_pred = (
        val_probabilities >= threshold
    ).astype(np.int32)

    acc = accuracy_score(
        y_val,
        val_pred
    )

    precision = precision_score(
        y_val,
        val_pred,
        zero_division=0
    )

    recall = recall_score(
        y_val,
        val_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_val,
        val_pred,
        zero_division=0
    )

    balanced_acc = balanced_accuracy_score(
        y_val,
        val_pred
    )

    threshold_results.append({
        "Threshold": threshold,
        "Accuracy": acc,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "Balanced_Accuracy": balanced_acc,
    })


threshold_df = pd.DataFrame(
    threshold_results
)

# Select threshold using validation balanced accuracy.
best_row = threshold_df.loc[
    threshold_df["Balanced_Accuracy"].idxmax()
]

final_threshold = float(
    best_row["Threshold"]
)

print("\nBest validation threshold:")
print(
    f"{final_threshold:.2f}"
)

print("\nValidation performance at selected threshold:")

print(
    f"Accuracy          : "
    f"{best_row['Accuracy'] * 100:.4f}%"
)

print(
    f"Precision         : "
    f"{best_row['Precision'] * 100:.4f}%"
)

print(
    f"Recall            : "
    f"{best_row['Recall'] * 100:.4f}%"
)

print(
    f"F1-score          : "
    f"{best_row['F1'] * 100:.4f}%"
)

print(
    f"Balanced Accuracy : "
    f"{best_row['Balanced_Accuracy'] * 100:.4f}%"
)

threshold_df.to_csv(
    RESULT_DIR / "validation_threshold_search.csv",
    index=False
)


# ============================================================
# 25. FREEZE THRESHOLD
# ============================================================

print("\nThreshold frozen at:")
print(final_threshold)


# ============================================================
# 26. FINAL TEST EVALUATION
# ============================================================

print("\n" + "=" * 80)
print("FINAL PRIMARY DNN TEST")
print("=" * 80)

test_start = time.perf_counter()

test_probabilities = model.predict(
    X_test_scaled,
    batch_size=8192,
    verbose=1
).reshape(-1)

test_end = time.perf_counter()

inference_time = (
    test_end - test_start
)

if not np.isfinite(test_probabilities).all():
    raise ValueError(
        "Test probabilities contain NaN/Inf."
    )

if (
    np.min(test_probabilities) < 0
    or np.max(test_probabilities) > 1
):
    raise ValueError(
        "Test probabilities outside [0,1]."
    )

y_test_pred = (
    test_probabilities >= final_threshold
).astype(np.int32)


# ============================================================
# 27. TEST METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_test_pred
)

precision = precision_score(
    y_test,
    y_test_pred,
    zero_division=0
)

recall = recall_score(
    y_test,
    y_test_pred,
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_test_pred,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    test_probabilities
)

pr_auc = average_precision_score(
    y_test,
    test_probabilities
)

balanced_accuracy = balanced_accuracy_score(
    y_test,
    y_test_pred
)

cm = confusion_matrix(
    y_test,
    y_test_pred,
    labels=[0, 1]
)

tn, fp, fn, tp = cm.ravel()

specificity = (
    tn / (tn + fp)
    if (tn + fp) > 0
    else 0
)

fpr = (
    fp / (fp + tn)
    if (fp + tn) > 0
    else 0
)

fnr = (
    fn / (fn + tp)
    if (fn + tp) > 0
    else 0
)


# ============================================================
# 28. PRINT FINAL RESULTS
# ============================================================

print("\n" + "=" * 80)
print("FINAL PRIMARY DNN RESULTS")
print("=" * 80)

print(
    f"\nDecision threshold : "
    f"{final_threshold:.2f}"
)

print("\nPRIMARY METRICS")
print("-" * 80)

print(
    f"Accuracy          : "
    f"{accuracy * 100:.4f}%"
)

print(
    f"Precision         : "
    f"{precision * 100:.4f}%"
)

print(
    f"Attack Recall     : "
    f"{recall * 100:.4f}%"
)

print(
    f"F1-score          : "
    f"{f1 * 100:.4f}%"
)

print(
    f"ROC-AUC           : "
    f"{roc_auc * 100:.4f}%"
)

print(
    f"PR-AUC            : "
    f"{pr_auc * 100:.4f}%"
)

print(
    f"Balanced Accuracy : "
    f"{balanced_accuracy * 100:.4f}%"
)

print("\nCONFUSION MATRIX")
print("-" * 80)

print(cm)

print("\nTN:", f"{tn:,}")
print("FP:", f"{fp:,}")
print("FN:", f"{fn:,}")
print("TP:", f"{tp:,}")

print("\nOPERATIONAL METRICS")
print("-" * 80)

print(
    f"Specificity         : "
    f"{specificity * 100:.4f}%"
)

print(
    f"False Positive Rate : "
    f"{fpr * 100:.4f}%"
)

print(
    f"False Negative Rate : "
    f"{fnr * 100:.4f}%"
)

print("\nINFERENCE")
print("-" * 80)

print(
    f"Total inference time : "
    f"{inference_time:.4f} seconds"
)

print(
    "Average time/sample :",
    f"{(inference_time / len(X_test)) * 1000:.6f} ms"
)

print("\nCLASSIFICATION REPORT")
print("-" * 80)

print(
    classification_report(
        y_test,
        y_test_pred,
        target_names=[
            "BENIGN",
            "ATTACK"
        ],
        digits=6,
        zero_division=0
    )
)


# ============================================================
# 29. SAVE FINAL METRICS
# ============================================================

metrics_df = pd.DataFrame([
    {
        "Model": "SecureSense Primary DNN",
        "Evaluation": "Stratified Held-Out Test",
        "Test_Samples": len(y_test),
        "Features": 69,
        "Threshold": final_threshold,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
        "Balanced_Accuracy": balanced_accuracy,
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
        "Specificity": specificity,
        "False_Positive_Rate": fpr,
        "False_Negative_Rate": fnr,
        "Training_Time_Seconds": training_time,
        "Inference_Time_Seconds": inference_time,
        "Inference_Time_ms_per_Sample":
            (inference_time / len(X_test)) * 1000,
    }
])

metrics_df.to_csv(
    METRICS_PATH,
    index=False
)


# ============================================================
# 30. SAVE CONFUSION MATRIX
# ============================================================

confusion_df = pd.DataFrame(
    cm,
    index=[
        "Actual_BENIGN",
        "Actual_ATTACK"
    ],
    columns=[
        "Predicted_BENIGN",
        "Predicted_ATTACK"
    ]
)

confusion_df.to_csv(
    CONFUSION_PATH
)


# ============================================================
# 31. SAVE CLASSIFICATION REPORT
# ============================================================

classification_dict = classification_report(
    y_test,
    y_test_pred,
    target_names=[
        "BENIGN",
        "ATTACK"
    ],
    output_dict=True,
    zero_division=0
)

classification_df = (
    pd.DataFrame(
        classification_dict
    ).transpose()
)

classification_df.to_csv(
    REPORT_PATH
)


# ============================================================
# 32. SAVE FINAL MODEL
# ============================================================

print("\nSaving final primary DNN model...")

model.save(
    FINAL_MODEL_PATH
)

print("Model saved:")
print(FINAL_MODEL_PATH)


# ============================================================
# 33. SAVE SCALER
# ============================================================

with open(
    FINAL_SCALER_PATH,
    "wb"
) as f:

    pickle.dump(
        scaler,
        f
    )

print("\nScaler saved:")
print(FINAL_SCALER_PATH)


# ============================================================
# 34. SAVE THRESHOLD
# ============================================================

with open(
    FINAL_THRESHOLD_PATH,
    "wb"
) as f:

    pickle.dump(
        final_threshold,
        f
    )

print("\nThreshold saved:")
print(FINAL_THRESHOLD_PATH)


# ============================================================
# 35. SAVE CONFIGURATION
# ============================================================

configuration = {
    "project": "SecureSense",
    "model": "Deep Neural Network",
    "architecture": "MLP / DNN",
    "input_features": 69,
    "hidden_layers": [
        {
            "units": 256,
            "activation": "relu",
            "dropout": 0.30,
        },
        {
            "units": 128,
            "activation": "relu",
            "dropout": 0.25,
        },
        {
            "units": 64,
            "activation": "relu",
            "dropout": 0.20,
        },
        {
            "units": 32,
            "activation": "relu",
        },
    ],
    "output": {
        "units": 1,
        "activation": "sigmoid",
    },
    "loss": "binary_crossentropy",
    "optimizer": "Adam",
    "initial_learning_rate": 0.001,
    "batch_size": 4096,
    "max_epochs": 15,
    "early_stopping_patience": 3,
    "reduce_lr_factor": 0.5,
    "validation_threshold_metric": "balanced_accuracy",
    "random_seed": SEED,
    "split_method": "stratified",
    "split_ratio": {
        "train": len(y_train) if "y_train" in locals() else None,
        "validation": len(y_val) if "y_val" in locals() else None,
        "test": len(y_test),
    },
    "training_time_seconds": training_time,
    "final_threshold": final_threshold,
    "test_metrics": {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "balanced_accuracy": balanced_accuracy,
        "specificity": specificity,
        "false_positive_rate": fpr,
        "false_negative_rate": fnr,
    },
}

with open(
    CONFIG_PATH,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        configuration,
        f,
        indent=4
    )

print("\nConfiguration saved:")
print(CONFIG_PATH)


# ============================================================
# 36. FINAL STATUS
# ============================================================

print("\n" + "=" * 80)
print("FINAL PRIMARY DNN TRAINING COMPLETE")
print("=" * 80)

print("\nPrimary model:")
print(FINAL_MODEL_PATH)

print("\nPrimary scaler:")
print(FINAL_SCALER_PATH)

print("\nPrimary threshold:")
print(FINAL_THRESHOLD_PATH)

print("\nPrimary metrics:")
print(METRICS_PATH)

print("\nResearch evidence directory:")
print(RESULT_DIR)

print("\n" + "=" * 80)
print("IMPORTANT")
print("=" * 80)

print(
    "\nThis primary DNN uses a stratified held-out evaluation."
)

print(
    "The earlier source-disjoint unseen-DDoS experiment "
    "remains separate research evidence."
)

print(
    "\nDO NOT retrain again automatically."
)

print(
    "Review the final results before making any further "
    "model changes."
)

print("\n" + "=" * 80)