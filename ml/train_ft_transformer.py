import os
import time
import pickle
import random

import numpy as np
import pandas as pd

import torch
import torch.nn as nn

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)

from rtdl_revisiting_models import FTTransformer


# ============================================================
# 1. PATHS
# ============================================================

BASE_DIR = r"W:\FinalYearProject\SecureSense_Project"

TRAIN_PATH = os.path.join(
    BASE_DIR,
    "notebooks",
    "data",
    "final_group_splits",
    "train.parquet",
)

TEST_PATH = os.path.join(
    BASE_DIR,
    "notebooks",
    "data",
    "final_group_splits",
    "test.parquet",
)

FEATURE_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_feature_names.pkl",
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_ft_transformer.pt",
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_ft_transformer_scaler.pkl",
)

THRESHOLD_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_ft_transformer_threshold.pkl",
)

RESULT_PATH = os.path.join(
    BASE_DIR,
    "results",
    "final_ft_transformer_metrics.csv",
)

CONFIG_PATH = os.path.join(
    BASE_DIR,
    "results",
    "final_ft_transformer_configuration.txt",
)


# ============================================================
# 2. SETTINGS
# ============================================================

RANDOM_STATE = 42

VALIDATION_SIZE = 0.10

NUM_FEATURES = 69

# FT-Transformer configuration
N_BLOCKS = 3
D_TOKEN = 64
ATTENTION_HEADS = 4

ATTENTION_DROPOUT = 0.20
FFN_DROPOUT = 0.10
RESIDUAL_DROPOUT = 0.00

FFN_MULTIPLIER = 4 / 3

LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-5

EPOCHS = 15
BATCH_SIZE = 4096
EVAL_BATCH_SIZE = 8192

PATIENCE = 3


# ============================================================
# 3. REPRODUCIBILITY
# ============================================================

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


set_seed(RANDOM_STATE)


# ============================================================
# 4. DEVICE
# ============================================================

DEVICE = torch.device("cpu")


# ============================================================
# 5. HEADER
# ============================================================

print("=" * 90)
print("SECURESENSE - FT-TRANSFORMER")
print("=" * 90)

print("\nPyTorch version:", torch.__version__)
print("Device:", DEVICE)

print("\nArchitecture:")
print("  Model        : FT-Transformer")
print("  Features     : 69 continuous")
print("  Blocks       :", N_BLOCKS)
print("  Token size   :", D_TOKEN)
print("  Heads        :", ATTENTION_HEADS)
print("  FFN          : ReGLU (library implementation)")
print("  Output head  : ReLU + Linear")
print("  Optimizer    : AdamW")
print("  Learning rate:", LEARNING_RATE)


# ============================================================
# 6. LOAD DATA
# ============================================================

print("\n[1/12] Loading datasets...")

train_df = pd.read_parquet(TRAIN_PATH)
test_df = pd.read_parquet(TEST_PATH)

print("Train shape:", train_df.shape)
print("Test shape :", test_df.shape)


# ============================================================
# 7. LOAD EXACT 69 FEATURES
# ============================================================

print("\n[2/12] Loading exact feature list...")

with open(FEATURE_PATH, "rb") as f:
    feature_names = list(pickle.load(f))

print("Number of features:", len(feature_names))

if len(feature_names) != NUM_FEATURES:
    raise RuntimeError(
        f"STOP: Expected {NUM_FEATURES} features, "
        f"found {len(feature_names)}."
    )

missing_train = [
    f for f in feature_names
    if f not in train_df.columns
]

missing_test = [
    f for f in feature_names
    if f not in test_df.columns
]

if missing_train:
    raise RuntimeError(
        f"STOP: Missing train features: {missing_train}"
    )

if missing_test:
    raise RuntimeError(
        f"STOP: Missing test features: {missing_test}"
    )

print("69-feature check: PASSED")


# ============================================================
# 8. LABEL CONVERSION
# ============================================================

print("\n[3/12] Converting labels...")


def convert_labels(series):
    labels = (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return np.where(
        labels == "BENIGN",
        0,
        1
    ).astype(np.int64)


y_full_train = convert_labels(train_df["Label"])
y_test = convert_labels(test_df["Label"])


# ============================================================
# 9. HARD DATASET SANITY CHECK
# ============================================================

print("\n" + "=" * 90)
print("DATASET SANITY CHECK")
print("=" * 90)

train_benign = np.sum(y_full_train == 0)
train_attack = np.sum(y_full_train == 1)

test_benign = np.sum(y_test == 0)
test_attack = np.sum(y_test == 1)

print("\nTRAIN")
print("BENIGN :", train_benign)
print("ATTACK :", train_attack)
print("TOTAL  :", len(y_full_train))

print("\nTEST")
print("BENIGN :", test_benign)
print("ATTACK :", test_attack)
print("TOTAL  :", len(y_test))

# Expected final group-aware split
if train_benign != 1347731:
    raise RuntimeError(
        f"STOP: Train benign count incorrect: {train_benign}"
    )

if train_attack != 208211:
    raise RuntimeError(
        f"STOP: Train attack count incorrect: {train_attack}"
    )

if test_benign != 547313:
    raise RuntimeError(
        f"STOP: Test benign count incorrect: {test_benign}"
    )

if test_attack != 128011:
    raise RuntimeError(
        f"STOP: Test attack count incorrect: {test_attack}"
    )

print("\n*** LABEL SANITY CHECK PASSED ***")


# ============================================================
# 10. FEATURE MATRICES
# ============================================================

print("\n[4/12] Preparing feature matrices...")

X_full_train = (
    train_df[feature_names]
    .astype(np.float32)
    .values
)

X_test = (
    test_df[feature_names]
    .astype(np.float32)
    .values
)

print("X_train:", X_full_train.shape)
print("X_test :", X_test.shape)


# ============================================================
# 11. NUMERICAL CHECK
# ============================================================

print("\nChecking numerical values...")

if not np.isfinite(X_full_train).all():
    raise RuntimeError(
        "STOP: Non-finite values in training data."
    )

if not np.isfinite(X_test).all():
    raise RuntimeError(
        "STOP: Non-finite values in test data."
    )

print("Numerical check: PASSED")


# ============================================================
# 12. VALIDATION SPLIT
# ============================================================

print("\n[5/12] Creating validation split...")

train_indices, val_indices = train_test_split(
    np.arange(len(y_full_train)),
    test_size=VALIDATION_SIZE,
    random_state=RANDOM_STATE,
    stratify=y_full_train,
)

X_train = X_full_train[train_indices]
y_train = y_full_train[train_indices]

X_val = X_full_train[val_indices]
y_val = y_full_train[val_indices]

print("Training samples  :", len(y_train))
print("Validation samples:", len(y_val))

print("\nTraining:")
print("BENIGN:", np.sum(y_train == 0))
print("ATTACK:", np.sum(y_train == 1))

print("\nValidation:")
print("BENIGN:", np.sum(y_val == 0))
print("ATTACK:", np.sum(y_val == 1))


# ============================================================
# 13. STANDARDIZATION
# ============================================================

print("\n[6/12] Scaling features...")

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train).astype(np.float32)
X_val = scaler.transform(X_val).astype(np.float32)
X_test = scaler.transform(X_test).astype(np.float32)

with open(SCALER_PATH, "wb") as f:
    pickle.dump(scaler, f)

print("Scaler saved.")


# ============================================================
# 14. CONVERT TO PYTORCH TENSORS
# ============================================================

print("\n[7/12] Converting data to tensors...")

X_train_tensor = torch.from_numpy(X_train)

# IMPORTANT:
# FT-Transformer returns logits with shape [batch, 1].
# Therefore labels are explicitly shaped [batch, 1].
y_train_tensor = torch.from_numpy(
    y_train.astype(np.float32).reshape(-1, 1)
)

X_val_tensor = torch.from_numpy(X_val)

y_val_tensor = torch.from_numpy(
    y_val.astype(np.float32).reshape(-1, 1)
)

X_test_tensor = torch.from_numpy(X_test)

y_test_tensor = torch.from_numpy(
    y_test.astype(np.float32).reshape(-1, 1)
)

print("Training tensor :", X_train_tensor.shape)
print("Training labels  :", y_train_tensor.shape)

print("Validation tensor:", X_val_tensor.shape)
print("Validation labels :", y_val_tensor.shape)

print("Test tensor      :", X_test_tensor.shape)
print("Test labels      :", y_test_tensor.shape)

# Hard shape verification
if y_train_tensor.ndim != 2 or y_train_tensor.shape[1] != 1:
    raise RuntimeError("STOP: Training labels must have shape [N, 1].")

if y_val_tensor.ndim != 2 or y_val_tensor.shape[1] != 1:
    raise RuntimeError("STOP: Validation labels must have shape [N, 1].")

print("Label tensor shape check: PASSED")


# ============================================================
# 15. BUILD FT-TRANSFORMER
# ============================================================

print("\n[8/12] Building FT-Transformer...")

model = FTTransformer(
    n_cont_features=NUM_FEATURES,
    cat_cardinalities=None,
    d_out=1,
    n_blocks=N_BLOCKS,
    d_block=D_TOKEN,
    attention_n_heads=ATTENTION_HEADS,
    attention_dropout=ATTENTION_DROPOUT,
    ffn_d_hidden=None,
    ffn_d_hidden_multiplier=FFN_MULTIPLIER,
    ffn_dropout=FFN_DROPOUT,
    residual_dropout=RESIDUAL_DROPOUT,
).to(DEVICE)

print(model)


# ============================================================
# 16. PARAMETER COUNT
# ============================================================

trainable_parameters = sum(
    p.numel()
    for p in model.parameters()
    if p.requires_grad
)

print("\nTrainable parameters:", trainable_parameters)


# ============================================================
# 17. OPTIMIZER
# ============================================================

optimizer = torch.optim.AdamW(
    model.make_parameter_groups(),
    lr=LEARNING_RATE,
    weight_decay=WEIGHT_DECAY,
)

loss_function = nn.BCEWithLogitsLoss()


# ============================================================
# 18. CONFIGURATION RECORD
# ============================================================

configuration_text = f"""
SECURESENSE FT-TRANSFORMER CONFIGURATION
========================================

Model:
FT-Transformer

Task:
Binary network intrusion classification

Input:
69 continuous numerical features

Categorical features:
None

Train samples:
{len(y_train)}

Validation samples:
{len(y_val)}

Test samples:
{len(y_test)}

Architecture:
Feature Tokenizer
-> [CLS] token
-> {N_BLOCKS} Transformer blocks
-> Classification head

Token dimension:
{D_TOKEN}

Attention heads:
{ATTENTION_HEADS}

Attention dropout:
{ATTENTION_DROPOUT}

FFN dropout:
{FFN_DROPOUT}

Residual dropout:
{RESIDUAL_DROPOUT}

FFN multiplier:
{FFN_MULTIPLIER}

Activation functions:
Transformer FFN: ReGLU
Classification head: ReLU
Final layer: Linear logit

Output:
Single logit

Probability conversion:
Sigmoid applied to model logits during evaluation

Loss:
Binary Cross Entropy with Logits

Optimizer:
AdamW

Learning rate:
{LEARNING_RATE}

Weight decay:
{WEIGHT_DECAY}

Batch size:
{BATCH_SIZE}

Epochs:
{EPOCHS}

Validation split:
{VALIDATION_SIZE}

Random state:
{RANDOM_STATE}

Device:
{DEVICE}

Trainable parameters:
{trainable_parameters}
"""

with open(CONFIG_PATH, "w", encoding="utf-8") as f:
    f.write(configuration_text)

print("\nConfiguration saved:")
print(CONFIG_PATH)


# ============================================================
# 19. BATCH ITERATOR
# ============================================================

def create_batches(
    X,
    y,
    batch_size,
    shuffle=False,
):
    n = len(X)

    if shuffle:
        indices = torch.randperm(n)
    else:
        indices = torch.arange(n)

    for start in range(0, n, batch_size):

        end = min(start + batch_size, n)

        batch_indices = indices[start:end]

        yield (
            X[batch_indices],
            y[batch_indices],
        )


# ============================================================
# 20. PREDICTION FUNCTION
# ============================================================

@torch.no_grad()
def predict_probabilities(
    X,
    batch_size,
):

    model.eval()

    probabilities = []

    for start in range(0, len(X), batch_size):

        end = min(
            start + batch_size,
            len(X),
        )

        batch = X[start:end].to(DEVICE)

        logits = model(
            batch,
            None,
        )

        # Safety check
        if logits.ndim != 2 or logits.shape[1] != 1:
            raise RuntimeError(
                f"Unexpected model output shape: {logits.shape}"
            )

        probs = torch.sigmoid(logits)

        probabilities.append(
            probs.cpu().numpy()
        )

    return np.concatenate(
        probabilities
    ).ravel()


# ============================================================
# 21. VALIDATION METRICS
# ============================================================

def calculate_validation_f1(
    probabilities,
    labels,
    threshold,
):

    predictions = (
        probabilities >= threshold
    ).astype(np.int32)

    return f1_score(
        labels,
        predictions,
        zero_division=0,
    )


# ============================================================
# 22. TRAINING
# ============================================================

print("\n" + "=" * 90)
print("STARTING FT-TRANSFORMER TRAINING")
print("=" * 90)

best_val_loss = float("inf")
best_state = None
epochs_without_improvement = 0

start_time = time.time()

for epoch in range(1, EPOCHS + 1):

    model.train()

    epoch_loss = 0.0
    batch_count = 0

    epoch_start = time.time()

    for X_batch, y_batch in create_batches(
        X_train_tensor,
        y_train_tensor,
        BATCH_SIZE,
        shuffle=True,
    ):

        X_batch = X_batch.to(DEVICE)
        y_batch = y_batch.to(DEVICE)

        optimizer.zero_grad()

        logits = model(
            X_batch,
            None,
        )

        # Final safety check before loss
        if logits.shape != y_batch.shape:
            raise RuntimeError(
                f"STOP: Shape mismatch before loss. "
                f"Logits={logits.shape}, Labels={y_batch.shape}"
            )

        loss = loss_function(
            logits,
            y_batch,
        )

        loss.backward()

        optimizer.step()

        epoch_loss += loss.item()
        batch_count += 1

    epoch_loss /= batch_count


    # --------------------------------------------------------
    # Validation loss
    # --------------------------------------------------------

    model.eval()

    validation_loss = 0.0
    validation_batches = 0

    with torch.no_grad():

        for X_batch, y_batch in create_batches(
            X_val_tensor,
            y_val_tensor,
            BATCH_SIZE,
            shuffle=False,
        ):

            X_batch = X_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            logits = model(
                X_batch,
                None,
            )

            if logits.shape != y_batch.shape:
                raise RuntimeError(
                    f"STOP: Validation shape mismatch. "
                    f"Logits={logits.shape}, Labels={y_batch.shape}"
                )

            loss = loss_function(
                logits,
                y_batch,
            )

            validation_loss += loss.item()
            validation_batches += 1

    validation_loss /= validation_batches

    epoch_time = time.time() - epoch_start

    print(f"\nEpoch {epoch}/{EPOCHS}")
    print(f"Train Loss: {epoch_loss:.6f}")
    print(f"Val Loss  : {validation_loss:.6f}")
    print(f"Time      : {epoch_time:.2f}s")


    # --------------------------------------------------------
    # Best model
    # --------------------------------------------------------

    if validation_loss < best_val_loss:

        best_val_loss = validation_loss

        best_state = {
            key: value.detach().cpu().clone()
            for key, value in model.state_dict().items()
        }

        epochs_without_improvement = 0

        print(">>> New best model")

    else:

        epochs_without_improvement += 1


    # --------------------------------------------------------
    # Early stopping
    # --------------------------------------------------------

    if epochs_without_improvement >= PATIENCE:

        print("\nEarly stopping triggered.")
        break


training_time = time.time() - start_time


# ============================================================
# 23. RESTORE BEST MODEL
# ============================================================

print("\nRestoring best validation model...")

if best_state is None:
    raise RuntimeError(
        "STOP: No best model was saved."
    )

model.load_state_dict(best_state)
model.to(DEVICE)

print("Best validation loss:", best_val_loss)
print(
    "Total training time:",
    round(training_time, 2),
    "seconds",
)


# ============================================================
# 24. VALIDATION PREDICTIONS
# ============================================================

print("\n[9/12] Generating validation predictions...")

val_probabilities = predict_probabilities(
    X_val_tensor,
    EVAL_BATCH_SIZE,
)


# ============================================================
# 25. THRESHOLD OPTIMIZATION
# ============================================================

print("\n[10/12] Finding validation threshold...")

best_threshold = 0.50
best_val_f1 = -1.0

for threshold in np.arange(
    0.10,
    0.91,
    0.01,
):

    current_f1 = calculate_validation_f1(
        val_probabilities,
        y_val,
        threshold,
    )

    if current_f1 > best_val_f1:

        best_val_f1 = current_f1
        best_threshold = float(threshold)

print("\nBest validation threshold:", best_threshold)
print(
    "Validation F1:",
    f"{best_val_f1:.6f}",
)


# ============================================================
# 26. SAVE THRESHOLD
# ============================================================

with open(THRESHOLD_PATH, "wb") as f:
    pickle.dump(
        best_threshold,
        f,
    )


# ============================================================
# 27. FINAL TEST
# ============================================================

print("\n" + "=" * 90)
print("FINAL UNSEEN GROUP-AWARE TEST")
print("=" * 90)

test_probabilities = predict_probabilities(
    X_test_tensor,
    EVAL_BATCH_SIZE,
)

test_predictions = (
    test_probabilities >= best_threshold
).astype(np.int32)


# ============================================================
# 28. METRICS
# ============================================================

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

pr_auc = average_precision_score(
    y_test,
    test_probabilities,
)

cm = confusion_matrix(
    y_test,
    test_predictions,
    labels=[0, 1],
)


# ============================================================
# 29. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 90)
print("FINAL FT-TRANSFORMER RESULTS")
print("=" * 90)

print(
    f"Accuracy  : {accuracy:.6f} "
    f"({accuracy * 100:.2f}%)"
)

print(
    f"Precision : {precision:.6f} "
    f"({precision * 100:.2f}%)"
)

print(
    f"Recall    : {recall:.6f} "
    f"({recall * 100:.2f}%)"
)

print(
    f"F1 Score  : {f1:.6f} "
    f"({f1 * 100:.2f}%)"
)

print(
    f"ROC-AUC   : {roc_auc:.6f} "
    f"({roc_auc * 100:.2f}%)"
)

print(
    f"PR-AUC    : {pr_auc:.6f} "
    f"({pr_auc * 100:.2f}%)"
)

print(
    f"Threshold : {best_threshold:.2f}"
)

print(
    f"Training Time : "
    f"{training_time:.2f} seconds"
)

print("\nConfusion Matrix:")
print("                 Predicted")
print("                 BENIGN  ATTACK")
print(
    f"Actual BENIGN    "
    f"{cm[0,0]:7d} "
    f"{cm[0,1]:7d}"
)
print(
    f"Actual ATTACK    "
    f"{cm[1,0]:7d} "
    f"{cm[1,1]:7d}"
)


# ============================================================
# 30. RANDOM FOREST REFERENCE
# ============================================================

rf_accuracy = 0.929858852935776
rf_precision = 0.9918395725838914
rf_recall = 0.6351954128942044
rf_f1 = 0.7744295020762696
rf_roc_auc = 0.9652716858933946
rf_pr_auc = 0.8852951950523896


# ============================================================
# 31. COMPARISON
# ============================================================

comparison = pd.DataFrame([
    {
        "Model": "Random Forest",
        "Accuracy": rf_accuracy,
        "Precision": rf_precision,
        "Recall": rf_recall,
        "F1": rf_f1,
        "ROC_AUC": rf_roc_auc,
        "PR_AUC": rf_pr_auc,
    },
    {
        "Model": "FT-Transformer",
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
    },
])

print("\n" + "=" * 90)
print("RANDOM FOREST vs FT-TRANSFORMER")
print("=" * 90)

print(
    comparison.to_string(
        index=False,
        float_format=lambda x: f"{x:.6f}",
    )
)


# ============================================================
# 32. SAVE MODEL
# ============================================================

torch.save(
    {
        "model_state_dict": model.state_dict(),
        "feature_names": feature_names,
        "num_features": NUM_FEATURES,
        "d_token": D_TOKEN,
        "n_blocks": N_BLOCKS,
        "attention_heads": ATTENTION_HEADS,
        "attention_dropout": ATTENTION_DROPOUT,
        "ffn_dropout": FFN_DROPOUT,
        "residual_dropout": RESIDUAL_DROPOUT,
        "ffn_multiplier": FFN_MULTIPLIER,
        "threshold": best_threshold,
        "trainable_parameters": trainable_parameters,
    },
    MODEL_PATH,
)

print("\nModel saved:")
print(MODEL_PATH)

print("\nScaler saved:")
print(SCALER_PATH)

print("\nThreshold saved:")
print(THRESHOLD_PATH)


# ============================================================
# 33. SAVE METRICS
# ============================================================

results = pd.DataFrame([
    {
        "Model": "FT-Transformer",
        "Evaluation": "Final Group-Aware",
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
        "Threshold": best_threshold,
        "Training_Time_Seconds": training_time,
        "Features": NUM_FEATURES,
        "D_Token": D_TOKEN,
        "N_Blocks": N_BLOCKS,
        "Attention_Heads": ATTENTION_HEADS,
        "Trainable_Parameters": trainable_parameters,
    }
])

results.to_csv(
    RESULT_PATH,
    index=False,
)

print("\nMetrics saved:")
print(RESULT_PATH)


# ============================================================
# 34. FINAL STATUS
# ============================================================

print("\n" + "=" * 90)
print("SECURESENSE FT-TRANSFORMER COMPLETE")
print("=" * 90)

if accuracy > rf_accuracy:
    print(
        "\nFT-Transformer achieved higher accuracy "
        "than Random Forest."
    )
else:
    print(
        "\nFT-Transformer accuracy did not exceed "
        "Random Forest."
    )

print("\nDone.")