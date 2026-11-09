import os
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_curve,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score
)


# ============================================================
# SECURESENSE - FINAL ROC & PRECISION-RECALL CURVES
# ============================================================

BASE_DIR = r"W:\FinalYearProject\SecureSense_Project"

# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

CLEANED_DATA = os.path.join(
    BASE_DIR,
    "data",
    "cleaned",
    "securesense_final_binary.parquet"
)

GROUP_TEST = os.path.join(
    BASE_DIR,
    "notebooks",
    "data",
    "final_group_splits",
    "test.parquet"
)

FEATURE_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_feature_names.pkl"
)

PRIMARY_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "primary_dnn.keras"
)

PRIMARY_SCALER = os.path.join(
    BASE_DIR,
    "models",
    "primary_dnn_scaler.pkl"
)

FINAL_MODEL = os.path.join(
    BASE_DIR,
    "models",
    "final_dnn.keras"
)

FINAL_SCALER = os.path.join(
    BASE_DIR,
    "models",
    "final_dnn_scaler.pkl"
)

PRIMARY_THRESHOLD_PATH = os.path.join(
    BASE_DIR,
    "models",
    "primary_dnn_threshold.pkl"
)

FINAL_THRESHOLD_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_dnn_threshold.pkl"
)

RESULT_DIR = os.path.join(
    BASE_DIR,
    "results",
    "final_curves"
)

os.makedirs(RESULT_DIR, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

RANDOM_STATE = 42
VALIDATION_SIZE = 0.10
BATCH_SIZE = 8192

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


print("=" * 90)
print("SECURESENSE - FINAL ROC & PRECISION-RECALL CURVES")
print("=" * 90)

print("\nTensorFlow:", tf.__version__)


# ============================================================
# LOAD FEATURE LIST
# ============================================================

print("\n[1/8] Loading 69 model features...")

with open(FEATURE_PATH, "rb") as f:
    feature_names = list(pickle.load(f))

if len(feature_names) != 69:
    raise RuntimeError(
        f"Expected 69 model features, found {len(feature_names)}"
    )

print("Features:", len(feature_names))


# ============================================================
# HELPER - LOAD LABELS
# ============================================================

def get_binary_labels(df):

    labels = (
        df["BinaryLabel"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    invalid = set(labels.unique()) - {"BENIGN", "ATTACK"}

    if invalid:
        raise RuntimeError(
            f"Unexpected labels found: {invalid}"
        )

    return np.where(
        labels == "ATTACK",
        1,
        0
    ).astype(np.int32)


# ============================================================
# 1. PRIMARY STRATIFIED EVALUATION
# ============================================================

print("\n[2/8] Loading cleaned dataset for primary evaluation...")

df = pd.read_parquet(CLEANED_DATA)

print("Cleaned dataset shape:", df.shape)

y_full = get_binary_labels(df)

X_full = (
    df[feature_names]
    .astype(np.float32)
    .values
)

if not np.isfinite(X_full).all():
    raise RuntimeError(
        "Non-finite values detected in primary dataset."
    )

print("Total samples:", len(y_full))
print("BENIGN:", np.sum(y_full == 0))
print("ATTACK:", np.sum(y_full == 1))


# ------------------------------------------------------------
# Recreate the EXACT primary train/validation/test protocol
#
# Primary evidence:
# 80% training pool
# 10% validation
# 10% test
# random_state = 42
# stratified
# ------------------------------------------------------------

print("\nCreating stratified split...")

all_indices = np.arange(len(y_full))

train_val_indices, test_indices = train_test_split(
    all_indices,
    test_size=0.10,
    random_state=RANDOM_STATE,
    stratify=y_full
)

train_indices, val_indices = train_test_split(
    train_val_indices,
    test_size=VALIDATION_SIZE / 0.90,
    random_state=RANDOM_STATE,
    stratify=y_full[train_val_indices]
)

print("Training:", len(train_indices))
print("Validation:", len(val_indices))
print("Primary Test:", len(test_indices))


# ------------------------------------------------------------
# Primary test set
# ------------------------------------------------------------

X_primary_test = X_full[test_indices]
y_primary_test = y_full[test_indices]

print("\nPrimary test distribution:")
print("BENIGN:", np.sum(y_primary_test == 0))
print("ATTACK:", np.sum(y_primary_test == 1))


# ------------------------------------------------------------
# Load primary scaler
# ------------------------------------------------------------

print("\nLoading primary scaler...")

with open(PRIMARY_SCALER, "rb") as f:
    primary_scaler = pickle.load(f)

X_primary_scaled = primary_scaler.transform(
    X_primary_test
).astype(np.float32)


# ------------------------------------------------------------
# Load primary DNN
# ------------------------------------------------------------

print("Loading primary DNN...")

primary_model = tf.keras.models.load_model(
    PRIMARY_MODEL,
    compile=False
)


# ------------------------------------------------------------
# Primary probabilities
# ------------------------------------------------------------

print("Generating primary probabilities...")

primary_probabilities = (
    primary_model.predict(
        X_primary_scaled,
        batch_size=BATCH_SIZE,
        verbose=1
    )
    .reshape(-1)
)

primary_roc_auc = roc_auc_score(
    y_primary_test,
    primary_probabilities
)

primary_pr_auc = average_precision_score(
    y_primary_test,
    primary_probabilities
)

print("\nPRIMARY RESULTS")
print("-" * 50)
print(f"ROC-AUC : {primary_roc_auc:.6f}")
print(f"PR-AUC  : {primary_pr_auc:.6f}")


# ============================================================
# 2. UNSEEN-SOURCE EVALUATION
# ============================================================

print("\n[3/8] Loading unseen-source test set...")

unseen_df = pd.read_parquet(GROUP_TEST)

print("Unseen-source shape:", unseen_df.shape)

y_unseen = get_binary_labels(unseen_df)

X_unseen = (
    unseen_df[feature_names]
    .astype(np.float32)
    .values
)

if not np.isfinite(X_unseen).all():
    raise RuntimeError(
        "Non-finite values detected in unseen-source dataset."
    )

print("BENIGN:", np.sum(y_unseen == 0))
print("ATTACK:", np.sum(y_unseen == 1))


# ------------------------------------------------------------
# Load final unseen-source scaler
# ------------------------------------------------------------

print("\nLoading final DNN scaler...")

with open(FINAL_SCALER, "rb") as f:
    final_scaler = pickle.load(f)

X_unseen_scaled = final_scaler.transform(
    X_unseen
).astype(np.float32)


# ------------------------------------------------------------
# Load FINAL source-disjoint DNN
# ------------------------------------------------------------

print("Loading final source-disjoint DNN...")

final_model = tf.keras.models.load_model(
    FINAL_MODEL,
    compile=False
)


# ------------------------------------------------------------
# Generate unseen-source probabilities
# ------------------------------------------------------------

print("Generating unseen-source probabilities...")

unseen_probabilities = (
    final_model.predict(
        X_unseen_scaled,
        batch_size=BATCH_SIZE,
        verbose=1
    )
    .reshape(-1)
)

unseen_roc_auc = roc_auc_score(
    y_unseen,
    unseen_probabilities
)

unseen_pr_auc = average_precision_score(
    y_unseen,
    unseen_probabilities
)

print("\nUNSEEN-SOURCE RESULTS")
print("-" * 50)
print(f"ROC-AUC : {unseen_roc_auc:.6f}")
print(f"PR-AUC  : {unseen_pr_auc:.6f}")


# ============================================================
# 3. GENERATE ROC CURVES
# ============================================================

print("\n[4/8] Generating ROC curves...")

primary_fpr, primary_tpr, _ = roc_curve(
    y_primary_test,
    primary_probabilities
)

unseen_fpr, unseen_tpr, _ = roc_curve(
    y_unseen,
    unseen_probabilities
)


# ============================================================
# 4. GENERATE PRECISION-RECALL CURVES
# ============================================================

print("[5/8] Generating Precision-Recall curves...")

primary_precision, primary_recall, _ = precision_recall_curve(
    y_primary_test,
    primary_probabilities
)

unseen_precision, unseen_recall, _ = precision_recall_curve(
    y_unseen,
    unseen_probabilities
)


# ============================================================
# 5. SAVE RAW CURVE DATA
# ============================================================

print("[6/8] Saving raw curve data...")


pd.DataFrame({
    "FPR": primary_fpr,
    "TPR": primary_tpr
}).to_csv(
    os.path.join(
        RESULT_DIR,
        "primary_roc_curve.csv"
    ),
    index=False
)


pd.DataFrame({
    "FPR": unseen_fpr,
    "TPR": unseen_tpr
}).to_csv(
    os.path.join(
        RESULT_DIR,
        "unseen_source_roc_curve.csv"
    ),
    index=False
)


pd.DataFrame({
    "Recall": primary_recall,
    "Precision": primary_precision
}).to_csv(
    os.path.join(
        RESULT_DIR,
        "primary_pr_curve.csv"
    ),
    index=False
)


pd.DataFrame({
    "Recall": unseen_recall,
    "Precision": unseen_precision
}).to_csv(
    os.path.join(
        RESULT_DIR,
        "unseen_source_pr_curve.csv"
    ),
    index=False
)


# ============================================================
# 6. FIGURE 6 - ROC CURVE
# ============================================================

print("[7/8] Creating Figure 6 - ROC Curve...")

plt.figure(figsize=(8, 6))

plt.plot(
    primary_fpr,
    primary_tpr,
    linewidth=2.2,
    label=f"Stratified Evaluation (AUC = {primary_roc_auc:.4f})"
)

plt.plot(
    unseen_fpr,
    unseen_tpr,
    linewidth=2.2,
    label=f"Unseen-Source Evaluation (AUC = {unseen_roc_auc:.4f})"
)

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    linewidth=1.2,
    label="Random Classifier"
)

plt.xlabel("False Positive Rate", fontsize=12)
plt.ylabel("True Positive Rate", fontsize=12)

plt.title(
    "ROC Curves for SecureSense DNN",
    fontsize=13,
    fontweight="bold"
)

plt.legend(
    loc="lower right",
    fontsize=10
)

plt.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.6
)

plt.xlim(0, 1)
plt.ylim(0, 1.01)

plt.tight_layout()

roc_path = os.path.join(
    RESULT_DIR,
    "Figure_6_ROC_Curves.png"
)

plt.savefig(
    roc_path,
    dpi=600,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 7. FIGURE 7 - PRECISION-RECALL CURVE
# ============================================================

print("[8/8] Creating Figure 7 - Precision-Recall Curve...")

plt.figure(figsize=(8, 6))

plt.plot(
    primary_recall,
    primary_precision,
    linewidth=2.2,
    label=f"Stratified Evaluation (AP = {primary_pr_auc:.4f})"
)

plt.plot(
    unseen_recall,
    unseen_precision,
    linewidth=2.2,
    label=f"Unseen-Source Evaluation (AP = {unseen_pr_auc:.4f})"
)

plt.xlabel("Recall", fontsize=12)
plt.ylabel("Precision", fontsize=12)

plt.title(
    "Precision-Recall Curves for SecureSense DNN",
    fontsize=13,
    fontweight="bold"
)

plt.legend(
    loc="lower left",
    fontsize=10
)

plt.grid(
    True,
    linestyle=":",
    linewidth=0.7,
    alpha=0.6
)

plt.xlim(0, 1)
plt.ylim(0, 1.01)

plt.tight_layout()

pr_path = os.path.join(
    RESULT_DIR,
    "Figure_7_PR_Curves.png"
)

plt.savefig(
    pr_path,
    dpi=600,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# 8. FINAL VERIFICATION
# ============================================================

print("\n" + "=" * 90)
print("CURVE GENERATION COMPLETE")
print("=" * 90)

print("\nPRIMARY STRATIFIED EVALUATION")
print(f"ROC-AUC : {primary_roc_auc:.6f}")
print(f"PR-AUC  : {primary_pr_auc:.6f}")

print("\nEXPECTED PRIMARY VALUES")
print("ROC-AUC : approximately 0.999653")
print("PR-AUC  : approximately 0.998579")

print("\nUNSEEN-SOURCE EVALUATION")
print(f"ROC-AUC : {unseen_roc_auc:.6f}")
print(f"PR-AUC  : {unseen_pr_auc:.6f}")

print("\nEXPECTED UNSEEN-SOURCE VALUES")
print("ROC-AUC : approximately 0.901464")
print("PR-AUC  : approximately 0.767094")

print("\nOUTPUT DIRECTORY:")
print(RESULT_DIR)

print("\nGenerated files:")
print("1. Figure_6_ROC_Curves.png")
print("2. Figure_7_PR_Curves.png")
print("3. primary_roc_curve.csv")
print("4. unseen_source_roc_curve.csv")
print("5. primary_pr_curve.csv")
print("6. unseen_source_pr_curve.csv")

print("\nIMPORTANT:")
print("- No model training was performed.")
print("- No threshold was changed.")
print("- Primary DNN is used only for primary evaluation.")
print("- Final DNN is used only for unseen-source evaluation.")
print("- ROC/PR curves use continuous probability outputs.")
print("- Classification thresholds are NOT used to calculate AUC.")
print("=" * 90)