import os
import time
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
)
from sklearn.utils.class_weight import compute_sample_weight

from pytorch_tabnet.tab_model import TabNetClassifier


# ============================================================
# SECURESENSE - TABNET DEEP LEARNING EXPERIMENT
# ============================================================

print("=" * 80)
print("SECURESENSE - TABNET DEEP LEARNING")
print("=" * 80)

TRAIN_PATH = "notebooks/data/final_group_splits/train.parquet"
TEST_PATH = "notebooks/data/final_group_splits/test.parquet"

MODEL_DIR = "models"
RESULTS_DIR = "results"

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


# ============================================================
# 1. LOAD DATA
# ============================================================

print("\n[1/7] Loading final group-aware data...")

train_df = pd.read_parquet(TRAIN_PATH)
test_df = pd.read_parquet(TEST_PATH)

print("Train shape:", train_df.shape)
print("Test shape :", test_df.shape)


# ============================================================
# 2. PREPARE FEATURES
# ============================================================

print("\n[2/7] Preparing 69 features...")

DROP_COLUMNS = [
    "Label",
    "_source_file",
    "BinaryLabel"
]

FEATURE_COLUMNS = [
    col for col in train_df.columns
    if col not in DROP_COLUMNS
]

print("Number of features:", len(FEATURE_COLUMNS))

X = train_df[FEATURE_COLUMNS].astype(np.float32)
y = train_df["BinaryLabel"].map({
    "BENIGN": 0,
    "ATTACK": 1
}).astype(np.int64)

X_test = test_df[FEATURE_COLUMNS].astype(np.float32)

y_test = test_df["BinaryLabel"].map({
    "BENIGN": 0,
    "ATTACK": 1
}).astype(np.int64)

# ============================================================
# 3. TRAIN / VALIDATION SPLIT
# ============================================================

print("\n[3/7] Creating validation split...")

X_train, X_val, y_train, y_val = train_test_split(
    X,
    y,
    test_size=0.10,
    stratify=y,
    random_state=42
)

print("Training rows  :", len(X_train))
print("Validation rows:", len(X_val))
print("Test rows      :", len(X_test))


# ============================================================
# 4. STANDARDIZATION
# ============================================================

print("\n[4/7] Scaling features...")

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train).astype(np.float32)
X_val = scaler.transform(X_val).astype(np.float32)
X_test_scaled = scaler.transform(X_test).astype(np.float32)

joblib.dump(
    scaler,
    os.path.join(MODEL_DIR, "tabnet_scaler.pkl")
)

joblib.dump(
    FEATURE_COLUMNS,
    os.path.join(MODEL_DIR, "tabnet_feature_names.pkl")
)

print("Scaling completed.")


# ============================================================
# 5. CLASS WEIGHTS
# ============================================================

print("\n[5/7] Calculating balanced sample weights...")

sample_weights = compute_sample_weight(
    class_weight="balanced",
    y=y_train
)

print("Class distribution:")
print(y_train.value_counts().to_dict())


# ============================================================
# 6. CREATE TABNET
# ============================================================

print("\n[6/7] Initializing TabNet...")

model = TabNetClassifier(
    n_d=32,
    n_a=32,
    n_steps=3,
    gamma=1.5,
    lambda_sparse=1e-4,
    optimizer_fn=__import__("torch").optim.Adam,
    optimizer_params=dict(
        lr=2e-2
    ),
    mask_type="entmax",
    seed=42,
    verbose=1
)

print("TabNet configuration:")
print("  n_d              = 32")
print("  n_a              = 32")
print("  n_steps          = 3")
print("  gamma            = 1.5")
print("  lambda_sparse    = 1e-4")
print("  learning rate    = 0.02")
print("  mask type        = entmax")


# ============================================================
# 7. TRAIN
# ============================================================

print("\n[7/7] Training TabNet...")
print("CPU training may take some time.")

start_time = time.time()

model.fit(
    X_train=X_train,
    y_train=y_train.to_numpy(),
    eval_set=[
        (X_train, y_train.to_numpy()),
        (X_val, y_val.to_numpy())
    ],
    eval_name=[
        "train",
        "valid"
    ],
    eval_metric=[
        "auc"
    ],
    max_epochs=30,
    patience=5,
    batch_size=8192,
    virtual_batch_size=1024,
    num_workers=0,
    drop_last=False,
    weights=sample_weights
)

training_time = time.time() - start_time

print("\nTraining completed.")
print(f"Training time: {training_time:.2f} seconds")


# ============================================================
# 8. TEST SET EVALUATION
# ============================================================

print("\nEvaluating on the UNSEEN-SOURCE test set...")

y_pred = model.predict(X_test_scaled).astype(int).ravel()

y_prob = model.predict_proba(X_test_scaled)[:, 1]


accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, y_prob)
pr_auc = average_precision_score(y_test, y_prob)


# ============================================================
# 9. RESULTS
# ============================================================

print("\n" + "=" * 80)
print("TABNET FINAL RESULTS")
print("=" * 80)

print(f"Accuracy : {accuracy * 100:.2f}%")
print(f"Precision: {precision * 100:.2f}%")
print(f"Recall   : {recall * 100:.2f}%")
print(f"F1 Score : {f1 * 100:.2f}%")
print(f"ROC-AUC  : {roc_auc * 100:.2f}%")
print(f"PR-AUC   : {pr_auc * 100:.2f}%")
print(f"Training : {training_time:.2f} seconds")

print("\nClassification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        target_names=["BENIGN", "ATTACK"],
        digits=4
    )
)


# ============================================================
# 10. SAVE MODEL
# ============================================================

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "tabnet_final.pkl"
)

model.save_model(
    os.path.join(MODEL_DIR, "tabnet_final")
)

print("\nModel saved to:")
print(MODEL_PATH)


# ============================================================
# 11. SAVE METRICS
# ============================================================

metrics = pd.DataFrame([{
    "Model": "TabNet",
    "Evaluation": "Final Group-Aware",
    "Accuracy": accuracy,
    "Precision": precision,
    "Recall": recall,
    "F1": f1,
    "ROC_AUC": roc_auc,
    "PR_AUC": pr_auc,
    "Training_Time_Seconds": training_time
}])

metrics_path = os.path.join(
    RESULTS_DIR,
    "tabnet_metrics.csv"
)

metrics.to_csv(metrics_path, index=False)

print("Metrics saved to:")
print(metrics_path)

print("\n" + "=" * 80)
print("TABNET EXPERIMENT COMPLETE")
print("=" * 80)