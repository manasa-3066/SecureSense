import os
import time
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf

from tensorflow.keras import Sequential
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    BatchNormalization,
    MaxPooling1D,
    LSTM,
    Dense,
    Dropout
)
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)

# ============================================================
# SECURESENSE - CNN-LSTM DEEP LEARNING EXPERIMENT
# ============================================================

print("=" * 80)
print("SECURESENSE - CNN-LSTM DEEP LEARNING MODEL")
print("=" * 80)

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = r"W:\FinalYearProject\SecureSense_Project"

TRAIN_PATH = os.path.join(
    BASE_DIR,
    "notebooks",
    "data",
    "final_group_splits",
    "train.parquet"
)

TEST_PATH = os.path.join(
    BASE_DIR,
    "notebooks",
    "data",
    "final_group_splits",
    "test.parquet"
)

MODEL_DIR = os.path.join(BASE_DIR, "models")
RESULT_DIR = os.path.join(BASE_DIR, "results")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "cnn_lstm_securesense.keras"
)

SCALER_PATH = os.path.join(
    MODEL_DIR,
    "cnn_lstm_scaler.pkl"
)

METRICS_PATH = os.path.join(
    RESULT_DIR,
    "cnn_lstm_metrics.csv"
)

# ------------------------------------------------------------
# REPRODUCIBILITY
# ------------------------------------------------------------

SEED = 42

np.random.seed(SEED)
tf.random.set_seed(SEED)

print("\nTensorFlow version:", tf.__version__)

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------

print("\nLoading training data...")
train_df = pd.read_parquet(TRAIN_PATH)

print("Training rows:", len(train_df))
print("Training columns:", len(train_df.columns))

print("\nLoading test data...")
test_df = pd.read_parquet(TEST_PATH)

print("Test rows:", len(test_df))
print("Test columns:", len(test_df.columns))

# ------------------------------------------------------------
# LABEL
# ------------------------------------------------------------

LABEL_COLUMN = "Label"

if LABEL_COLUMN not in train_df.columns:
    raise ValueError("Label column not found in training data.")

if LABEL_COLUMN not in test_df.columns:
    raise ValueError("Label column not found in test data.")

# ------------------------------------------------------------
# FEATURES
# ------------------------------------------------------------

# ------------------------------------------------------------
# FEATURES
# ------------------------------------------------------------
# Use the exact 69 features used by the final Random Forest.
# This ensures a fair ML vs DL comparison.

FEATURE_NAMES_PATH = os.path.join(
    BASE_DIR,
    "models",
    "final_feature_names.pkl"
)

with open(FEATURE_NAMES_PATH, "rb") as f:
    feature_names = pickle.load(f)

print("\nNumber of model features:", len(feature_names))

if len(feature_names) != 69:
    raise ValueError(
        f"Expected 69 model features, but found {len(feature_names)}."
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
    raise ValueError(
        f"Missing training features: {missing_train}"
    )

if missing_test:
    raise ValueError(
        f"Missing test features: {missing_test}"
    )

print("All 69 Random Forest features are available.")
# ------------------------------------------------------------
# PREPARE X AND Y
# ------------------------------------------------------------

X_train = train_df[feature_names].astype(np.float32).values
X_test = test_df[feature_names].astype(np.float32).values

def convert_labels(labels):
    labels = labels.astype(str).str.upper()

    return np.where(
        labels == "ATTACK",
        1,
        0
    ).astype(np.int32)

y_train = convert_labels(train_df[LABEL_COLUMN])
y_test = convert_labels(test_df[LABEL_COLUMN])

print("\nClass distribution:")
print(
    "TRAIN -> BENIGN:",
    np.sum(y_train == 0),
    "| ATTACK:",
    np.sum(y_train == 1)
)

print(
    "TEST  -> BENIGN:",
    np.sum(y_test == 0),
    "| ATTACK:",
    np.sum(y_test == 1)
)

# ------------------------------------------------------------
# SCALE FEATURES
# ------------------------------------------------------------

print("\nScaling features...")

scaler = StandardScaler()

X_train = scaler.fit_transform(X_train).astype(np.float32)
X_test = scaler.transform(X_test).astype(np.float32)

# Save scaler for future inference
with open(SCALER_PATH, "wb") as f:
    pickle.dump(scaler, f)

print("Scaler saved.")

# ------------------------------------------------------------
# CNN-LSTM INPUT SHAPE
# ------------------------------------------------------------
#
# Each network-flow record is represented as a sequence
# of 69 numerical features.
#
# Shape:
#   samples x 69 features x 1 channel
#
# ------------------------------------------------------------

X_train = X_train.reshape(
    X_train.shape[0],
    X_train.shape[1],
    1
)

X_test = X_test.reshape(
    X_test.shape[0],
    X_test.shape[1],
    1
)

print("\nCNN-LSTM input shape:", X_train.shape)

# ------------------------------------------------------------
# CLASS WEIGHT
# ------------------------------------------------------------

negative = np.sum(y_train == 0)
positive = np.sum(y_train == 1)

class_weight = {
    0: 1.0,
    1: negative / positive
}

print("\nClass weights:")
print(class_weight)

# ------------------------------------------------------------
# BUILD CNN-LSTM
# ------------------------------------------------------------

print("\nBuilding CNN-LSTM model...")

model = Sequential([
    Input(shape=(69, 1)),

    Conv1D(
        filters=64,
        kernel_size=3,
        activation="relu",
        padding="same"
    ),

    BatchNormalization(),

    MaxPooling1D(
        pool_size=2
    ),

    Conv1D(
        filters=128,
        kernel_size=3,
        activation="relu",
        padding="same"
    ),

    BatchNormalization(),

    MaxPooling1D(
        pool_size=2
    ),

    LSTM(
        64,
        return_sequences=False
    ),

    Dense(
        64,
        activation="relu"
    ),

    Dropout(0.30),

    Dense(
        32,
        activation="relu"
    ),

    Dropout(0.20),

    Dense(
        1,
        activation="sigmoid"
    )
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy"
    ]
)

model.summary()

# ------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------

early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=2,
    min_lr=1e-6,
    verbose=1
)

# ------------------------------------------------------------
# TRAINING
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("STARTING CNN-LSTM TRAINING")
print("=" * 80)

start_time = time.time()

history = model.fit(
    X_train,
    y_train,

    validation_split=0.10,

    epochs=25,

    batch_size=2048,

    class_weight=class_weight,

    callbacks=[
        early_stopping,
        reduce_lr
    ],

    verbose=1
)

training_time = time.time() - start_time

print("\nTraining completed.")
print(
    "Training time:",
    round(training_time, 2),
    "seconds"
)

# ------------------------------------------------------------
# SAVE MODEL
# ------------------------------------------------------------

model.save(MODEL_PATH)

print("\nCNN-LSTM model saved:")
print(MODEL_PATH)

# ------------------------------------------------------------
# PREDICTION
# ------------------------------------------------------------

print("\nRunning test-set prediction...")

probabilities = model.predict(
    X_test,
    batch_size=4096,
    verbose=1
).ravel()

predictions = (
    probabilities >= 0.50
).astype(np.int32)

# ------------------------------------------------------------
# METRICS
# ------------------------------------------------------------

accuracy = accuracy_score(
    y_test,
    predictions
)

precision = precision_score(
    y_test,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_test,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_test,
    predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_test,
    probabilities
)

pr_auc = average_precision_score(
    y_test,
    probabilities
)

cm = confusion_matrix(
    y_test,
    predictions
)

# ------------------------------------------------------------
# RESULTS
# ------------------------------------------------------------

print("\n" + "=" * 80)
print("CNN-LSTM FINAL RESULTS")
print("=" * 80)

print(f"Accuracy   : {accuracy:.6f} ({accuracy * 100:.2f}%)")
print(f"Precision  : {precision:.6f} ({precision * 100:.2f}%)")
print(f"Recall     : {recall:.6f} ({recall * 100:.2f}%)")
print(f"F1 Score   : {f1:.6f} ({f1 * 100:.2f}%)")
print(f"ROC-AUC    : {roc_auc:.6f} ({roc_auc * 100:.2f}%)")
print(f"PR-AUC     : {pr_auc:.6f} ({pr_auc * 100:.2f}%)")
print(f"Training   : {training_time:.2f} seconds")

print("\nConfusion Matrix:")
print(cm)

# ------------------------------------------------------------
# COMPARE WITH RANDOM FOREST
# ------------------------------------------------------------

rf_accuracy = 0.929858852935776
rf_precision = 0.9918395725838914
rf_recall = 0.6351954128942044
rf_f1 = 0.7744295020762696
rf_roc_auc = 0.9652716858933946
rf_pr_auc = 0.8852951950523896

print("\n" + "=" * 80)
print("RANDOM FOREST vs CNN-LSTM")
print("=" * 80)

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
        "Model": "CNN-LSTM",
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
    }
])

print(
    comparison.to_string(
        index=False
    )
)

# ------------------------------------------------------------
# SAVE METRICS
# ------------------------------------------------------------

metrics_df = pd.DataFrame([{
    "Model": "CNN-LSTM",
    "Evaluation": "Final Group-Aware",
    "Accuracy": accuracy,
    "Precision": precision,
    "Recall": recall,
    "F1": f1,
    "ROC_AUC": roc_auc,
    "PR_AUC": pr_auc,
    "Training_Time_Seconds": training_time
}])

metrics_df.to_csv(
    METRICS_PATH,
    index=False
)

print("\nMetrics saved:")
print(METRICS_PATH)

print("\n" + "=" * 80)
print("CNN-LSTM EXPERIMENT COMPLETE")
print("=" * 80)