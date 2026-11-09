"""
SECURESENSE - CNN-LSTM SEQUENCE EXPERIMENT
==========================================

Purpose
-------
Evaluate a CNN-LSTM hybrid on CICIDS2017 network-flow sequences.

IMPORTANT DESIGN
----------------
Each timestep = one network flow.
Each timestep contains 69 SecureSense features.

Input:
    (sequence_length=10, features=69)

Architecture:
    Conv1D -> BatchNorm -> MaxPooling
           -> Conv1D -> BatchNorm
           -> LSTM
           -> Dense
           -> Sigmoid

The experiment preserves CICIDS2017 source-file boundaries.

FINAL GROUP-AWARE SPLIT
-----------------------
TRAIN:
    Botnet-Friday
    Bruteforce-Tuesday
    DoS-Wednesday
    Infiltration-Thursday
    Portscan-Friday
    WebAttacks-Thursday

TEST:
    Benign-Monday
    DDoS-Friday

The CNN-LSTM is a SEPARATE experiment.
It does not modify the deployed Random Forest.
"""

import os
import time
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import tensorflow as tf

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    classification_report,
)
from sklearn.utils.class_weight import compute_class_weight

from tensorflow.keras import Sequential
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    BatchNormalization,
    MaxPooling1D,
    LSTM,
    Dense,
    Dropout,
)
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
    ModelCheckpoint,
)
from tensorflow.keras.optimizers import Adam


warnings.filterwarnings("ignore")


# ============================================================
# 1. REPRODUCIBILITY
# ============================================================

SEED = 42

os.environ["PYTHONHASHSEED"] = str(SEED)

np.random.seed(SEED)
tf.random.set_seed(SEED)

try:
    tf.config.experimental.enable_op_determinism()
except Exception:
    pass


# ============================================================
# 2. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRAIN_PATH = (
    PROJECT_ROOT
    / "notebooks"
    / "data"
    / "final_group_splits"
    / "train.parquet"
)

TEST_PATH = (
    PROJECT_ROOT
    / "notebooks"
    / "data"
    / "final_group_splits"
    / "test.parquet"
)

FEATURE_FILE = (
    PROJECT_ROOT
    / "models"
    / "final_feature_names.pkl"
)

MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


MODEL_OUTPUT = (
    MODEL_DIR / "cnn_lstm_sequence_final.keras"
)

SCALER_OUTPUT = (
    MODEL_DIR / "cnn_lstm_sequence_scaler.pkl"
)

METRICS_OUTPUT = (
    RESULTS_DIR / "cnn_lstm_sequence_metrics.csv"
)

CONFUSION_OUTPUT = (
    RESULTS_DIR / "cnn_lstm_sequence_confusion_matrix.csv"
)

PREDICTIONS_OUTPUT = (
    RESULTS_DIR / "cnn_lstm_sequence_prediction_distribution.csv"
)


# ============================================================
# 3. EXPERIMENT CONFIGURATION
# ============================================================

SEQUENCE_LENGTH = 10

VALIDATION_FRACTION = 0.10

BATCH_SIZE = 512

FULL_EPOCHS = 20

PILOT_EPOCHS = 2

PILOT_SAMPLES = 30_000

LEARNING_RATE = 0.001


# ============================================================
# 4. EXPECTED SOURCE FILES
# ============================================================

EXPECTED_TRAIN_SOURCES = {
    "Botnet-Friday-no-metadata.parquet",
    "Bruteforce-Tuesday-no-metadata.parquet",
    "DoS-Wednesday-no-metadata.parquet",
    "Infiltration-Thursday-no-metadata.parquet",
    "Portscan-Friday-no-metadata.parquet",
    "WebAttacks-Thursday-no-metadata.parquet",
}

EXPECTED_TEST_SOURCES = {
    "Benign-Monday-no-metadata.parquet",
    "DDoS-Friday-no-metadata.parquet",
}


# ============================================================
# 5. LOAD FEATURE NAMES
# ============================================================

def load_feature_names():

    print("\n" + "=" * 80)
    print("LOADING FINAL FEATURE SCHEMA")
    print("=" * 80)

    if not FEATURE_FILE.exists():
        raise FileNotFoundError(
            f"Missing feature file:\n{FEATURE_FILE}"
        )

    with open(FEATURE_FILE, "rb") as f:
        feature_names = list(pickle.load(f))

    print("Feature file:", FEATURE_FILE)
    print("Number of features:", len(feature_names))

    if len(feature_names) != 69:
        raise ValueError(
            f"Expected 69 features, "
            f"but found {len(feature_names)}."
        )

    print("PASS: 69 features confirmed.")

    return feature_names


# ============================================================
# 6. LOAD COMBINED GROUP-AWARE DATA
# ============================================================

def load_grouped_data(path, feature_names, expected_sources):

    print("\n" + "=" * 80)
    print("LOADING")
    print("=" * 80)

    print(path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found:\n{path}"
        )

    columns = (
        feature_names
        + [
            "Label",
            "BinaryLabel",
            "_source_file",
        ]
    )

    df = pd.read_parquet(
        path,
        columns=columns
    )

    print("Rows:", len(df))
    print("Columns loaded:", len(df.columns))

    # --------------------------------------------------------
    # Verify required columns
    # --------------------------------------------------------

    required = set(
        feature_names
        + [
            "Label",
            "BinaryLabel",
            "_source_file",
        ]
    )

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns:\n{sorted(missing)}"
        )

    # --------------------------------------------------------
    # Verify source files
    # --------------------------------------------------------

    actual_sources = set(
        df["_source_file"]
        .dropna()
        .astype(str)
        .unique()
    )

    print("\nSource files found:")

    for source in sorted(actual_sources):
        print("  ", source)

    if actual_sources != expected_sources:

        print("\nEXPECTED:")
        for source in sorted(expected_sources):
            print("  ", source)

        print("\nACTUAL:")
        for source in sorted(actual_sources):
            print("  ", source)

        raise ValueError(
            "\nSource-file mismatch detected."
            "\nThe experiment has been stopped."
        )

    # --------------------------------------------------------
    # Verify BinaryLabel
    # --------------------------------------------------------

    binary_values = sorted(
        df["BinaryLabel"]
        .dropna()
        .unique()
        .tolist()
    )

    print(
        "\nBinaryLabel unique values:",
        binary_values
    )

    if set(binary_values) != {0, 1}:
        raise ValueError(
            "BinaryLabel must contain exactly 0 and 1."
        )

    # --------------------------------------------------------
    # Verify BinaryLabel against Label
    # --------------------------------------------------------

    label_text = (
        df["Label"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    expected_binary = (
        label_text != "BENIGN"
    ).astype(np.int8)

    actual_binary = (
        df["BinaryLabel"]
        .astype(np.int8)
    )

    mismatches = int(
        (expected_binary != actual_binary).sum()
    )

    print(
        "Label/BinaryLabel mismatches:",
        mismatches
    )

    if mismatches != 0:
        raise ValueError(
            "BinaryLabel does not consistently "
            "represent BENIGN vs ATTACK."
        )

    print(
        "PASS: BinaryLabel verified."
    )

    # --------------------------------------------------------
    # Verify numerical values
    # --------------------------------------------------------

    X = df[feature_names].apply(
        pd.to_numeric,
        errors="coerce"
    )

    invalid_mask = (
        ~np.isfinite(
            X.to_numpy(dtype=np.float64)
        ).all(axis=1)
    )

    invalid_count = int(
        invalid_mask.sum()
    )

    print(
        "Rows containing NaN/Inf:",
        invalid_count
    )

    if invalid_count != 0:
        raise ValueError(
            "NaN/Inf values detected. "
            "Do not continue until preprocessing is fixed."
        )

    # --------------------------------------------------------
    # Build source-wise arrays
    # --------------------------------------------------------

    source_data = {}

    for source, group in df.groupby(
        "_source_file",
        sort=False
    ):

        X_source = group[
            feature_names
        ].to_numpy(
            dtype=np.float32
        )

        y_source = group[
            "BinaryLabel"
        ].to_numpy(
            dtype=np.int8
        )

        source_data[source] = (
            X_source,
            y_source,
        )

        print(
            f"\n{source}"
        )

        print(
            "  Rows:",
            len(group)
        )

        print(
            "  BENIGN:",
            int((y_source == 0).sum())
        )

        print(
            "  ATTACK:",
            int((y_source == 1).sum())
        )

    del df

    return source_data


# ============================================================
# 7. FIT SCALER ONLY ON TRAINING PORTIONS
# ============================================================

def fit_training_scaler(train_sources):

    print("\n" + "=" * 80)
    print("FITTING STANDARD SCALER")
    print("=" * 80)

    scaler = StandardScaler()

    total_rows = 0

    for source, (X, y) in train_sources.items():

        split_index = int(
            len(X)
            * (1.0 - VALIDATION_FRACTION)
        )

        X_train_part = X[:split_index]

        scaler.partial_fit(
            X_train_part
        )

        total_rows += len(
            X_train_part
        )

        print(
            f"{source}: "
            f"{len(X_train_part):,} rows used"
        )

    print(
        "\nTotal rows used to fit scaler:",
        f"{total_rows:,}"
    )

    print(
        "PASS: scaler fitted ONLY on training portions."
    )

    return scaler


# ============================================================
# 8. SCALE SOURCE ARRAYS
# ============================================================

def scale_sources(source_data, scaler):

    scaled = {}

    for source, (X, y) in source_data.items():

        X_scaled = scaler.transform(
            X
        ).astype(
            np.float32
        )

        scaled[source] = (
            X_scaled,
            y
        )

    return scaled


# ============================================================
# 9. CREATE SEQUENCE DATASET FOR ONE SOURCE
# ============================================================

def create_source_dataset(
    X,
    y,
    start_target,
    end_target,
    shuffle,
):

    """
    Target i corresponds to the LAST flow in the
    sequence ending at i.

    Example for sequence length 10:

        Flow 1
        Flow 2
        ...
        Flow 10  -> target = Label(Flow 10)

    Therefore:

        input shape = (10, 69)
    """

    if end_target <= start_target:
        raise ValueError(
            "Invalid sequence range."
        )

    data_start = (
        start_target
        - SEQUENCE_LENGTH
        + 1
    )

    data_end = end_target

    data = X[
        data_start:data_end
    ]

    targets = y[
        start_target:end_target
    ]

    number_of_sequences = len(
        targets
    )

    if number_of_sequences <= 0:
        raise ValueError(
            "No sequences could be created."
        )

    dataset = tf.keras.utils.timeseries_dataset_from_array(
        data=data,
        targets=targets,
        sequence_length=SEQUENCE_LENGTH,
        sequence_stride=1,
        sampling_rate=1,
        batch_size=None,
        shuffle=shuffle,
        seed=SEED,
    )

    return dataset, number_of_sequences


# ============================================================
# 10. CREATE TRAIN / VALIDATION / TEST DATASETS
# ============================================================

def create_datasets(
    train_sources,
    test_sources,
    class_weights,
):

    print("\n" + "=" * 80)
    print("CREATING FLOW SEQUENCES")
    print("=" * 80)

    train_datasets = []
    validation_datasets = []
    test_datasets = []

    train_sequence_count = 0
    validation_sequence_count = 0
    test_sequence_count = 0

    # --------------------------------------------------------
    # TRAINING SOURCES
    # --------------------------------------------------------

    for source, (X, y) in train_sources.items():

        split_index = int(
            len(X)
            * (1.0 - VALIDATION_FRACTION)
        )

        # ----------------------------------------------------
        # TRAIN
        # ----------------------------------------------------

        train_ds, train_count = (
            create_source_dataset(
                X=X,
                y=y,
                start_target=SEQUENCE_LENGTH - 1,
                end_target=split_index,
                shuffle=True,
            )
        )

        train_ds = train_ds.map(
            lambda features, label: (
                features,
                label,
                tf.where(
                    tf.equal(label, 1),
                    tf.cast(
                        class_weights[1],
                        tf.float32
                    ),
                    tf.cast(
                        class_weights[0],
                        tf.float32
                    ),
                ),
            ),
            num_parallel_calls=tf.data.AUTOTUNE,
        )

        train_datasets.append(
            train_ds
        )

        train_sequence_count += (
            train_count
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        # We include the previous 9 training flows as
        # context for the first validation flow.
        validation_start = max(
            split_index,
            SEQUENCE_LENGTH - 1
        )

        validation_data_start = (
            validation_start
            - SEQUENCE_LENGTH
            + 1
        )

        validation_ds, val_count = (
            create_source_dataset(
                X=X,
                y=y,
                start_target=validation_start,
                end_target=len(y),
                shuffle=False,
            )
        )

        validation_datasets.append(
            validation_ds
        )

        validation_sequence_count += (
            val_count
        )

        print(
            f"\n{source}"
        )

        print(
            "  Train sequences:",
            f"{train_count:,}"
        )

        print(
            "  Validation sequences:",
            f"{val_count:,}"
        )

    # --------------------------------------------------------
    # TEST SOURCES
    # --------------------------------------------------------

    for source, (X, y) in test_sources.items():

        test_ds, test_count = (
            create_source_dataset(
                X=X,
                y=y,
                start_target=SEQUENCE_LENGTH - 1,
                end_target=len(y),
                shuffle=False,
            )
        )

        test_datasets.append(
            test_ds
        )

        test_sequence_count += (
            test_count
        )

        print(
            f"\n{source}"
        )

        print(
            "  Test sequences:",
            f"{test_count:,}"
        )

    # --------------------------------------------------------
    # Combine sources
    # --------------------------------------------------------

    train_ds = train_datasets[0]

    for ds in train_datasets[1:]:
        train_ds = train_ds.concatenate(ds)

    validation_ds = validation_datasets[0]

    for ds in validation_datasets[1:]:
        validation_ds = validation_ds.concatenate(ds)

    test_ds = test_datasets[0]

    for ds in test_datasets[1:]:
        test_ds = test_ds.concatenate(ds)

    # --------------------------------------------------------
    # Batch
    # --------------------------------------------------------

    train_ds = (
        train_ds
        .shuffle(
            20_000,
            seed=SEED,
            reshuffle_each_iteration=True,
        )
        .batch(
            BATCH_SIZE
        )
        .prefetch(
            tf.data.AUTOTUNE
        )
    )

    validation_ds = (
        validation_ds
        .batch(
            BATCH_SIZE
        )
        .prefetch(
            tf.data.AUTOTUNE
        )
    )

    test_ds = (
        test_ds
        .batch(
            BATCH_SIZE
        )
        .prefetch(
            tf.data.AUTOTUNE
        )
    )

    print("\n" + "-" * 80)

    print(
        "TOTAL TRAIN SEQUENCES:",
        f"{train_sequence_count:,}"
    )

    print(
        "TOTAL VALIDATION SEQUENCES:",
        f"{validation_sequence_count:,}"
    )

    print(
        "TOTAL TEST SEQUENCES:",
        f"{test_sequence_count:,}"
    )

    return (
        train_ds,
        validation_ds,
        test_ds,
    )


# ============================================================
# 11. CALCULATE CLASS WEIGHTS
# ============================================================

def calculate_class_weights(train_sources):

    print("\n" + "=" * 80)
    print("CALCULATING CLASS WEIGHTS")
    print("=" * 80)

    labels = []

    for source, (X, y) in train_sources.items():

        split_index = int(
            len(y)
            * (1.0 - VALIDATION_FRACTION)
        )

        # The first SEQUENCE_LENGTH-1 flows
        # cannot be sequence targets.
        sequence_labels = y[
            SEQUENCE_LENGTH - 1:
            split_index
        ]

        labels.append(
            sequence_labels
        )

    labels = np.concatenate(
        labels
    )

    classes = np.array(
        [0, 1]
    )

    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=labels,
    )

    class_weights = {
        0: float(weights[0]),
        1: float(weights[1]),
    }

    print(
        "Training sequence labels:"
    )

    print(
        "  BENIGN:",
        int((labels == 0).sum())
    )

    print(
        "  ATTACK:",
        int((labels == 1).sum())
    )

    print(
        "\nClass weights:"
    )

    print(
        "  BENIGN:",
        class_weights[0]
    )

    print(
        "  ATTACK:",
        class_weights[1]
    )

    return class_weights


# ============================================================
# 12. BUILD CNN-LSTM
# ============================================================

def build_cnn_lstm():

    print("\n" + "=" * 80)
    print("BUILDING CNN-LSTM")
    print("=" * 80)

    model = Sequential(
        [

            Input(
                shape=(
                    SEQUENCE_LENGTH,
                    69
                ),
                name="flow_sequence_input",
            ),

            # ------------------------------------------------
            # CNN - LOCAL PATTERN EXTRACTION
            # ------------------------------------------------

            Conv1D(
                filters=64,
                kernel_size=3,
                padding="same",
                activation="relu",
                name="cnn_local_features_1",
            ),

            BatchNormalization(
                name="batch_norm_1"
            ),

            MaxPooling1D(
                pool_size=2,
                name="max_pooling",
            ),

            Conv1D(
                filters=128,
                kernel_size=3,
                padding="same",
                activation="relu",
                name="cnn_local_features_2",
            ),

            BatchNormalization(
                name="batch_norm_2"
            ),

            # ------------------------------------------------
            # LSTM - SEQUENTIAL DEPENDENCY LEARNING
            # ------------------------------------------------

            LSTM(
                64,
                return_sequences=False,
                name="lstm_temporal_learning",
            ),

            Dropout(
                0.30,
                name="dropout_lstm",
            ),

            # ------------------------------------------------
            # CLASSIFICATION
            # ------------------------------------------------

            Dense(
                64,
                activation="relu",
                name="dense_classifier",
            ),

            Dropout(
                0.20,
                name="dropout_classifier",
            ),

            Dense(
                1,
                activation="sigmoid",
                name="binary_output",
            ),
        ],
        name="SecureSense_CNN_LSTM",
    )

    model.compile(
        optimizer=Adam(
            learning_rate=LEARNING_RATE
        ),
        loss="binary_crossentropy",
        metrics=[
            tf.keras.metrics.BinaryAccuracy(
                name="accuracy"
            ),
            tf.keras.metrics.Precision(
                name="precision"
            ),
            tf.keras.metrics.Recall(
                name="recall"
            ),
            tf.keras.metrics.AUC(
                name="roc_auc"
            ),
            tf.keras.metrics.AUC(
                name="pr_auc",
                curve="PR",
            ),
        ],
    )

    model.summary()

    return model


# ============================================================
# 13. PILOT CHECK
# ============================================================

def run_pilot_check(
    train_ds,
    validation_ds,
    class_weights,
):

    print("\n" + "=" * 80)
    print("PILOT CHECK")
    print("=" * 80)

    print(
        "This is a short learning check."
    )

    print(
        "It is NOT the final result."
    )

    print(
        f"Pilot samples: {PILOT_SAMPLES:,}"
    )

    pilot_model = build_cnn_lstm()

    # --------------------------------------------------------
    # Take a limited number of samples.
    # --------------------------------------------------------

    pilot_ds = (
        train_ds
        .unbatch()
        .take(PILOT_SAMPLES)
        .batch(BATCH_SIZE)
        .prefetch(tf.data.AUTOTUNE)
    )

    pilot_history = pilot_model.fit(
        pilot_ds,
        epochs=PILOT_EPOCHS,
        validation_data=validation_ds.take(100),
        verbose=1,
    )

    # --------------------------------------------------------
    # Pilot predictions
    # --------------------------------------------------------

    probabilities = (
        pilot_model
        .predict(
            pilot_ds.map(
                lambda x, y, w: x
            ),
            verbose=1,
        )
        .ravel()
    )

    predictions = (
        probabilities >= 0.50
    ).astype(
        np.int8
    )

    attack_predictions = int(
        (predictions == 1).sum()
    )

    benign_predictions = int(
        (predictions == 0).sum()
    )

    print("\n" + "-" * 80)
    print("PILOT PREDICTION CHECK")
    print("-" * 80)

    print(
        "BENIGN predictions:",
        benign_predictions
    )

    print(
        "ATTACK predictions:",
        attack_predictions
    )

    print(
        "ATTACK prediction percentage:",
        round(
            100
            * attack_predictions
            / len(predictions),
            2,
        ),
        "%"
    )

    # --------------------------------------------------------
    # DO NOT continue if model predicts only one class
    # --------------------------------------------------------

    if attack_predictions == 0:

        raise RuntimeError(
            "\n"
            "==================================================\n"
            "PILOT FAILED\n"
            "==================================================\n"
            "CNN-LSTM predicted ZERO ATTACK samples.\n\n"
            "FULL TRAINING HAS BEEN STOPPED.\n\n"
            "We will NOT waste hours on a model that is\n"
            "already showing the previous failure pattern.\n"
            "=================================================="
        )

    if benign_predictions == 0:

        raise RuntimeError(
            "\n"
            "PILOT FAILED\n"
            "CNN-LSTM predicted ZERO BENIGN samples.\n"
            "FULL TRAINING HAS BEEN STOPPED."
        )

    print(
        "\nPILOT PASSED."
    )

    print(
        "The model is producing both classes."
    )

    return pilot_model


# ============================================================
# 14. FULL TRAINING
# ============================================================

def train_full_model(
    train_ds,
    validation_ds,
):

    print("\n" + "=" * 80)
    print("FULL CNN-LSTM TRAINING")
    print("=" * 80)

    model = build_cnn_lstm()

    callbacks = [

        EarlyStopping(
            monitor="val_pr_auc",
            mode="max",
            patience=4,
            restore_best_weights=True,
            verbose=1,
        ),

        ReduceLROnPlateau(
            monitor="val_pr_auc",
            mode="max",
            factor=0.5,
            patience=2,
            min_lr=1e-6,
            verbose=1,
        ),

        ModelCheckpoint(
            filepath=MODEL_OUTPUT,
            monitor="val_pr_auc",
            mode="max",
            save_best_only=True,
            verbose=1,
        ),
    ]

    start_time = time.time()

    history = model.fit(
        train_ds,
        validation_data=validation_ds,
        epochs=FULL_EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    training_time = (
        time.time() - start_time
    )

    print(
        "\nTraining time:",
        round(training_time, 2),
        "seconds"
    )

    # --------------------------------------------------------
    # Load best checkpoint
    # --------------------------------------------------------

    if MODEL_OUTPUT.exists():

        print(
            "\nLoading best validation model:"
        )

        print(
            MODEL_OUTPUT
        )

        model = tf.keras.models.load_model(
            MODEL_OUTPUT
        )

    return model, training_time, history


# ============================================================
# 15. FINAL EVALUATION
# ============================================================

def evaluate_final_model(
    model,
    test_ds,
    training_time,
):

    print("\n" + "=" * 80)
    print("FINAL UNSEEN-SOURCE EVALUATION")
    print("=" * 80)

    # --------------------------------------------------------
    # Collect predictions
    # --------------------------------------------------------

    probabilities = (
        model
        .predict(
            test_ds.map(
                lambda x, y, w: x
            ),
            verbose=1,
        )
        .ravel()
    )

    # Collect actual labels
    actual_labels = []

    for _, y, _ in test_ds:

        actual_labels.append(
            y.numpy()
        )

    y_test = np.concatenate(
        actual_labels
    )

    predictions = (
        probabilities >= 0.50
    ).astype(
        np.int8
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        predictions
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

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\n" + "-" * 80)
    print("CNN-LSTM FINAL RESULTS")
    print("-" * 80)

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
        f"ROC-AUC   : {roc_auc:.6f}"
    )

    print(
        f"PR-AUC    : {pr_auc:.6f}"
    )

    print(
        f"Training Time: {training_time:.2f} seconds"
    )

    print("\nCONFUSION MATRIX")

    print(cm)

    print("\nCLASSIFICATION REPORT")

    print(
        classification_report(
            y_test,
            predictions,
            target_names=[
                "BENIGN",
                "ATTACK",
            ],
            zero_division=0,
        )
    )

    # --------------------------------------------------------
    # Prediction distribution
    # --------------------------------------------------------

    benign_count = int(
        (predictions == 0).sum()
    )

    attack_count = int(
        (predictions == 1).sum()
    )

    print(
        "Predicted BENIGN:",
        benign_count
    )

    print(
        "Predicted ATTACK:",
        attack_count
    )

    print(
        "Predicted ATTACK percentage:",
        round(
            100
            * attack_count
            / len(predictions),
            2,
        ),
        "%"
    )

    # --------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------

    metrics_df = pd.DataFrame(
        [
            {
                "Model": "CNN-LSTM",
                "Evaluation": "Final Group-Aware",
                "Sequence_Length": SEQUENCE_LENGTH,
                "Features_Per_Flow": 69,
                "Accuracy": accuracy,
                "Precision": precision,
                "Recall": recall,
                "F1": f1,
                "ROC_AUC": roc_auc,
                "PR_AUC": pr_auc,
                "Training_Time_Seconds": training_time,
            }
        ]
    )

    metrics_df.to_csv(
        METRICS_OUTPUT,
        index=False
    )

    # --------------------------------------------------------
    # Save confusion matrix
    # --------------------------------------------------------

    cm_df = pd.DataFrame(
        cm,
        index=[
            "Actual_BENIGN",
            "Actual_ATTACK",
        ],
        columns=[
            "Predicted_BENIGN",
            "Predicted_ATTACK",
        ],
    )

    cm_df.to_csv(
        CONFUSION_OUTPUT
    )

    # --------------------------------------------------------
    # Save prediction distribution
    # --------------------------------------------------------

    prediction_df = pd.DataFrame(
        [
            {
                "Prediction": "BENIGN",
                "Count": benign_count,
                "Percentage": (
                    100
                    * benign_count
                    / len(predictions)
                ),
            },
            {
                "Prediction": "ATTACK",
                "Count": attack_count,
                "Percentage": (
                    100
                    * attack_count
                    / len(predictions)
                ),
            },
        ]
    )

    prediction_df.to_csv(
        PREDICTIONS_OUTPUT,
        index=False
    )

    print("\nSaved:")

    print(
        METRICS_OUTPUT
    )

    print(
        CONFUSION_OUTPUT
    )

    print(
        PREDICTIONS_OUTPUT
    )

    return {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
        "ROC_AUC": roc_auc,
        "PR_AUC": pr_auc,
    }


# ============================================================
# 16. MAIN
# ============================================================

def main():

    total_start = time.time()

    print("\n")
    print("=" * 80)
    print("SECURESENSE - CNN-LSTM SEQUENCE EXPERIMENT")
    print("=" * 80)

    print(
        "TensorFlow:",
        tf.__version__
    )

    gpus = tf.config.list_physical_devices(
        "GPU"
    )

    if gpus:

        print(
            "GPU detected:",
            gpus
        )

    else:

        print(
            "No GPU detected. TensorFlow will use CPU."
        )

    # --------------------------------------------------------
    # Feature schema
    # --------------------------------------------------------

    feature_names = (
        load_feature_names()
    )

    # --------------------------------------------------------
    # Load TRAIN
    # --------------------------------------------------------

    train_sources = (
        load_grouped_data(
            TRAIN_PATH,
            feature_names,
            EXPECTED_TRAIN_SOURCES,
        )
    )

    # --------------------------------------------------------
    # Load TEST
    # --------------------------------------------------------

    test_sources = (
        load_grouped_data(
            TEST_PATH,
            feature_names,
            EXPECTED_TEST_SOURCES,
        )
    )

    # --------------------------------------------------------
    # Fit scaler
    # --------------------------------------------------------

    scaler = (
        fit_training_scaler(
            train_sources
        )
    )

    with open(
        SCALER_OUTPUT,
        "wb"
    ) as f:

        pickle.dump(
            scaler,
            f
        )

    print(
        "\nScaler saved:",
        SCALER_OUTPUT
    )

    # --------------------------------------------------------
    # Scale
    # --------------------------------------------------------

    train_sources = (
        scale_sources(
            train_sources,
            scaler,
        )
    )

    test_sources = (
        scale_sources(
            test_sources,
            scaler,
        )
    )

    print(
        "PASS: all sources scaled using "
        "the training-only scaler."
    )

    # --------------------------------------------------------
    # Class weights
    # --------------------------------------------------------

    class_weights = (
        calculate_class_weights(
            train_sources
        )
    )

    # --------------------------------------------------------
    # Datasets
    # --------------------------------------------------------

    (
        train_ds,
        validation_ds,
        test_ds,
    ) = create_datasets(
        train_sources,
        test_sources,
        class_weights,
    )

    # --------------------------------------------------------
    # PILOT
    # --------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("IMPORTANT: RUNNING PILOT BEFORE FULL TRAINING")
    print("=" * 80)

    run_pilot_check(
        train_ds,
        validation_ds,
        class_weights,
    )

    # --------------------------------------------------------
    # FULL TRAINING
    # --------------------------------------------------------

    model, training_time, history = (
        train_full_model(
            train_ds,
            validation_ds,
        )
    )

    # --------------------------------------------------------
    # FINAL TEST
    # --------------------------------------------------------

    results = (
        evaluate_final_model(
            model,
            test_ds,
            training_time,
        )
    )

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    total_time = (
        time.time()
        - total_start
    )

    print("\n" + "=" * 80)
    print("CNN-LSTM EXPERIMENT COMPLETED")
    print("=" * 80)

    print(
        f"Total experiment time: "
        f"{total_time:.2f} seconds"
    )

    print("\nFINAL METRICS")

    for metric, value in results.items():

        if metric in [
            "Accuracy",
            "Precision",
            "Recall",
            "F1",
        ]:

            print(
                f"{metric:10s}: "
                f"{value:.4f} "
                f"({value * 100:.2f}%)"
            )

        else:

            print(
                f"{metric:10s}: "
                f"{value:.4f}"
            )

    print("\nModel:")
    print(MODEL_OUTPUT)

    print(
        "\nExisting Random Forest was NOT modified."
    )

    print("\nDone.")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()