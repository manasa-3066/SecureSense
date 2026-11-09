"""
SECURESENSE
CNN-LSTM HYBRID EXPERIMENT

Purpose:
    Evaluate a CNN-LSTM hybrid on the final group-aware
    CICIDS2017 binary intrusion-detection split.

Important:
    - BinaryLabel is used for BENIGN / ATTACK.
    - Label is NOT used because it contains attack-family names.
    - 69 final features are used.
    - Sequences are created only within the same source file.
    - Test sources remain completely unseen during training.
"""

import os
import time
import pickle
import gc

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
)

from tensorflow.keras import Sequential
from tensorflow.keras.layers import (
    Input,
    Conv1D,
    MaxPooling1D,
    LSTM,
    Dense,
    Dropout,
    BatchNormalization,
)
from tensorflow.keras.callbacks import (
    EarlyStopping,
    ReduceLROnPlateau,
)


# ============================================================
# CONFIGURATION
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
    "final_cnn_lstm.keras",
)

SCALER_PATH = os.path.join(
    BASE_DIR,
    "models",
    "cnn_lstm_scaler.pkl",
)

METRICS_PATH = os.path.join(
    BASE_DIR,
    "results",
    "final_cnn_lstm_metrics.csv",
)


# ============================================================
# EXPERIMENT SETTINGS
# ============================================================

SEED = 42

# Number of consecutive network flows in one sequence.
SEQUENCE_LENGTH = 10

# Use every 5th possible training window.
#
# This prevents the training set from becoming unnecessarily
# enormous because adjacent windows overlap heavily.
#
# Validation and test use stride 1.
TRAIN_STRIDE = 5
VAL_STRIDE = 1
TEST_STRIDE = 1

# 10% of each training source is reserved for validation.
VALIDATION_FRACTION = 0.10

# Keep this moderate because TensorFlow is running on CPU.
EPOCHS = 10

BATCH_SIZE = 2048

LEARNING_RATE = 0.001


# ============================================================
# REPRODUCIBILITY
# ============================================================

np.random.seed(SEED)
tf.random.set_seed(SEED)


# ============================================================
# START
# ============================================================

print("=" * 90)
print("SECURESENSE - FINAL CNN-LSTM HYBRID EXPERIMENT")
print("=" * 90)

print("\nTensorFlow:", tf.__version__)


# ============================================================
# GPU CHECK
# ============================================================

gpus = tf.config.list_physical_devices("GPU")

if gpus:
    print("GPU detected:", gpus)
else:
    print("No GPU detected. TensorFlow will use CPU.")


# ============================================================
# LOAD FEATURE SCHEMA
# ============================================================

print("\n" + "=" * 90)
print("1. LOADING FINAL FEATURE SCHEMA")
print("=" * 90)


with open(FEATURE_PATH, "rb") as f:
    feature_names = pickle.load(f)

feature_names = list(feature_names)

print("Number of features:", len(feature_names))


if len(feature_names) != 69:
    raise RuntimeError(
        f"Expected exactly 69 features, "
        f"but found {len(feature_names)}."
    )

print("PASS: 69 features confirmed.")


# ============================================================
# LOAD DATA
# ============================================================

print("\n" + "=" * 90)
print("2. LOADING FINAL GROUP-AWARE DATA")
print("=" * 90)

print("Train:", TRAIN_PATH)
print("Test :", TEST_PATH)


train_df = pd.read_parquet(TRAIN_PATH)
test_df = pd.read_parquet(TEST_PATH)


print("\nTrain shape:", train_df.shape)
print("Test shape :", test_df.shape)


# ============================================================
# VERIFY REQUIRED COLUMNS
# ============================================================

required_columns = (
    feature_names
    + [
        "Label",
        "_source_file",
        "BinaryLabel",
    ]
)


for column in required_columns:

    if column not in train_df.columns:
        raise RuntimeError(
            f"Missing training column: {column}"
        )

    if column not in test_df.columns:
        raise RuntimeError(
            f"Missing testing column: {column}"
        )


print(
    "PASS: Required columns are present."
)


# ============================================================
# VERIFY SOURCE GROUPS
# ============================================================

print("\n" + "=" * 90)
print("3. VERIFYING SOURCE GROUPS")
print("=" * 90)


train_sources = sorted(
    train_df["_source_file"]
    .astype(str)
    .unique()
)

test_sources = sorted(
    test_df["_source_file"]
    .astype(str)
    .unique()
)


print("\nTraining sources:")

for source in train_sources:
    print("  ", source)


print("\nTesting sources:")

for source in test_sources:
    print("  ", source)


# These are the final source groups already established
# for SecureSense.

expected_train_sources = {
    "Botnet-Friday-no-metadata.parquet",
    "Bruteforce-Tuesday-no-metadata.parquet",
    "DoS-Wednesday-no-metadata.parquet",
    "Infiltration-Thursday-no-metadata.parquet",
    "Portscan-Friday-no-metadata.parquet",
    "WebAttacks-Thursday-no-metadata.parquet",
}

expected_test_sources = {
    "Benign-Monday-no-metadata.parquet",
    "DDoS-Friday-no-metadata.parquet",
}


if set(train_sources) != expected_train_sources:

    raise RuntimeError(
        "\nTraining source mismatch.\n"
        f"Expected: {sorted(expected_train_sources)}\n"
        f"Found   : {train_sources}"
    )


if set(test_sources) != expected_test_sources:

    raise RuntimeError(
        "\nTesting source mismatch.\n"
        f"Expected: {sorted(expected_test_sources)}\n"
        f"Found   : {test_sources}"
    )


overlap = (
    set(train_sources)
    &
    set(test_sources)
)


if overlap:

    raise RuntimeError(
        f"Source leakage detected: {overlap}"
    )


print(
    "\nPASS: No source overlap between train and test."
)


# ============================================================
# BINARY LABEL PREPARATION
# ============================================================

print("\n" + "=" * 90)
print("4. BINARY LABEL PREPARATION")
print("=" * 90)


def convert_binary_labels(series):

    labels = (
        series
        .astype(str)
        .str.strip()
        .str.upper()
    )

    unique_labels = set(
        labels.unique()
    )

    print(
        "Binary labels found:",
        sorted(unique_labels)
    )

    expected = {
        "BENIGN",
        "ATTACK",
    }

    invalid = (
        unique_labels
        -
        expected
    )

    if invalid:

        raise RuntimeError(
            f"Unexpected BinaryLabel values: {invalid}"
        )

    return np.where(
        labels == "ATTACK",
        1,
        0
    ).astype(np.int32)


# IMPORTANT:
#
# We deliberately use BinaryLabel.
#
# Label contains values such as:
# PORTSCAN
# BOT
# DOS HULK
# SSH-PATATOR
# etc.
#
# BinaryLabel contains:
# BENIGN
# ATTACK


train_df["Target"] = convert_binary_labels(
    train_df["BinaryLabel"]
)

test_df["Target"] = convert_binary_labels(
    test_df["BinaryLabel"]
)


print("\nBENIGN -> 0")
print("ATTACK -> 1")


# ============================================================
# VERIFY FINAL CLASS DISTRIBUTION
# ============================================================

print("\nTraining class distribution:")

train_benign = int(
    np.sum(
        train_df["Target"].values == 0
    )
)

train_attack = int(
    np.sum(
        train_df["Target"].values == 1
    )
)

print("BENIGN:", train_benign)
print("ATTACK:", train_attack)


print("\nTesting class distribution:")

test_benign = int(
    np.sum(
        test_df["Target"].values == 0
    )
)

test_attack = int(
    np.sum(
        test_df["Target"].values == 1
    )
)

print("BENIGN:", test_benign)
print("ATTACK:", test_attack)


if train_benign == 0 or train_attack == 0:
    raise RuntimeError(
        "Training data contains only one class."
    )

if test_benign == 0 or test_attack == 0:
    raise RuntimeError(
        "Testing data contains only one class."
    )


# ============================================================
# PREPARE NUMERICAL FEATURES
# ============================================================

print("\n" + "=" * 90)
print("5. PREPARING NUMERICAL FEATURES")
print("=" * 90)


X_train_raw = (
    train_df[feature_names]
    .to_numpy(dtype=np.float32)
)

X_test_raw = (
    test_df[feature_names]
    .to_numpy(dtype=np.float32)
)


y_train_all = (
    train_df["Target"]
    .to_numpy(dtype=np.int32)
)

y_test_all = (
    test_df["Target"]
    .to_numpy(dtype=np.int32)
)


if not np.isfinite(X_train_raw).all():

    raise RuntimeError(
        "Training features contain NaN or infinite values."
    )


if not np.isfinite(X_test_raw).all():

    raise RuntimeError(
        "Testing features contain NaN or infinite values."
    )


print(
    "Training feature matrix:",
    X_train_raw.shape
)

print(
    "Testing feature matrix:",
    X_test_raw.shape
)

print(
    "PASS: No NaN or infinite values."
)


# ============================================================
# FIT SCALER ONLY ON TRAINING DATA
# ============================================================

print("\n" + "=" * 90)
print("6. FEATURE SCALING")
print("=" * 90)


scaler = StandardScaler()

scaler.fit(
    X_train_raw
)


X_train_scaled = scaler.transform(
    X_train_raw
).astype(np.float32)


X_test_scaled = scaler.transform(
    X_test_raw
).astype(np.float32)


with open(
    SCALER_PATH,
    "wb"
) as f:

    pickle.dump(
        scaler,
        f
    )


print(
    "PASS: StandardScaler fitted only on training data."
)


# ============================================================
# SOURCE BOUNDARIES
# ============================================================

def get_source_boundaries(dataframe):

    source_values = (
        dataframe["_source_file"]
        .astype(str)
        .to_numpy()
    )

    boundaries = []

    start = 0

    for i in range(
        1,
        len(source_values)
    ):

        if source_values[i] != source_values[i - 1]:

            boundaries.append(
                (
                    source_values[start],
                    start,
                    i
                )
            )

            start = i


    boundaries.append(
        (
            source_values[start],
            start,
            len(source_values)
        )
    )

    return boundaries


train_boundaries = get_source_boundaries(
    train_df
)

test_boundaries = get_source_boundaries(
    test_df
)


print("\nTraining source boundaries:")

for source, start, end in train_boundaries:

    print(
        f"  {source}: "
        f"rows {start} -> {end - 1} "
        f"({end - start:,} rows)"
    )


print("\nTesting source boundaries:")

for source, start, end in test_boundaries:

    print(
        f"  {source}: "
        f"rows {start} -> {end - 1} "
        f"({end - start:,} rows)"
    )


# ============================================================
# TRAIN / VALIDATION SOURCE-LOCAL WINDOWS
# ============================================================

print("\n" + "=" * 90)
print("7. DEFINING SEQUENCE WINDOWS")
print("=" * 90)


def create_window_metadata(
    boundaries,
    labels,
    sequence_length,
    stride,
    validation_fraction=None,
):
    """
    Creates compact metadata only.

    It DOES NOT create the actual sequence tensors.

    Each window contains:
        sequence_length consecutive flows

    The label is the label of the final flow.

    Windows never cross source-file boundaries.
    """

    metadata = []

    for source, start, end in boundaries:

        n_rows = end - start

        if n_rows < sequence_length:
            continue

        if validation_fraction is not None:

            split_point = (
                start
                +
                int(
                    n_rows
                    *
                    (1.0 - validation_fraction)
                )
            )

            # Training windows remain completely
            # inside the training portion of this source.

            train_start = start
            train_end = split_point

            if (
                train_end
                -
                train_start
                >= sequence_length
            ):

                first_end = (
                    train_start
                    +
                    sequence_length
                    -
                    1
                )

                last_end = (
                    train_end
                    -
                    1
                )

                metadata.append(
                    {
                        "source": source,
                        "start": train_start,
                        "end": train_end,
                        "first_end": first_end,
                        "last_end": last_end,
                        "stride": stride,
                    }
                )


            # Validation windows are constructed entirely
            # inside the validation part.

            val_start = split_point
            val_end = end

            if (
                val_end
                -
                val_start
                >= sequence_length
            ):

                first_end = (
                    val_start
                    +
                    sequence_length
                    -
                    1
                )

                last_end = (
                    val_end
                    -
                    1
                )

                # Store separately by using source marker.

                metadata.append(
                    {
                        "source": source,
                        "start": val_start,
                        "end": val_end,
                        "first_end": first_end,
                        "last_end": last_end,
                        "stride": stride,
                    }
                )

        else:

            first_end = (
                start
                +
                sequence_length
                -
                1
            )

            last_end = end - 1

            metadata.append(
                {
                    "source": source,
                    "start": start,
                    "end": end,
                    "first_end": first_end,
                    "last_end": last_end,
                    "stride": stride,
                }
            )

    return metadata


# ------------------------------------------------------------
# We create train and validation metadata separately.
# ------------------------------------------------------------

def create_partition_metadata(
    boundaries,
    sequence_length,
    stride,
    validation_fraction,
    partition,
):

    metadata = []

    for source, start, end in boundaries:

        n_rows = end - start

        if n_rows < sequence_length:
            continue

        split_point = (
            start
            +
            int(
                n_rows
                *
                (1.0 - validation_fraction)
            )
        )

        if partition == "train":

            part_start = start
            part_end = split_point

        elif partition == "validation":

            part_start = split_point
            part_end = end

        else:

            raise ValueError(
                "partition must be train or validation"
            )


        if (
            part_end
            -
            part_start
            <
            sequence_length
        ):
            continue


        first_end = (
            part_start
            +
            sequence_length
            -
            1
        )

        last_end = part_end - 1


        metadata.append(
            {
                "source": source,
                "start": part_start,
                "end": part_end,
                "first_end": first_end,
                "last_end": last_end,
                "stride": stride,
            }
        )

    return metadata


train_meta = create_partition_metadata(
    train_boundaries,
    SEQUENCE_LENGTH,
    TRAIN_STRIDE,
    VALIDATION_FRACTION,
    "train",
)


val_meta = create_partition_metadata(
    train_boundaries,
    SEQUENCE_LENGTH,
    VAL_STRIDE,
    VALIDATION_FRACTION,
    "validation",
)


test_meta = []


for source, start, end in test_boundaries:

    if end - start < SEQUENCE_LENGTH:
        continue

    test_meta.append(
        {
            "source": source,
            "start": start,
            "end": end,
            "first_end": (
                start
                +
                SEQUENCE_LENGTH
                -
                1
            ),
            "last_end": end - 1,
            "stride": TEST_STRIDE,
        }
    )


# ============================================================
# COUNT WINDOWS
# ============================================================

def count_windows(metadata):

    total = 0

    for item in metadata:

        total += (
            (
                item["last_end"]
                -
                item["first_end"]
            )
            //
            item["stride"]
        ) + 1

    return total


train_window_count = count_windows(
    train_meta
)

val_window_count = count_windows(
    val_meta
)

test_window_count = count_windows(
    test_meta
)


print(
    "\nSequence length:",
    SEQUENCE_LENGTH
)

print(
    "Training stride:",
    TRAIN_STRIDE
)

print(
    "Validation stride:",
    VAL_STRIDE
)

print(
    "Test stride:",
    TEST_STRIDE
)

print(
    "\nTraining windows:",
    f"{train_window_count:,}"
)

print(
    "Validation windows:",
    f"{val_window_count:,}"
)

print(
    "Test windows:",
    f"{test_window_count:,}"
)


# ============================================================
# SEQUENCE BATCH GENERATOR
# ============================================================

class SequenceBatchGenerator(
    tf.keras.utils.Sequence
):

    def __init__(
        self,
        X,
        y,
        metadata,
        batch_size,
        sequence_length,
        shuffle=False,
        seed=42,
    ):

        self.X = X
        self.y = y
        self.metadata = metadata
        self.batch_size = batch_size
        self.sequence_length = sequence_length
        self.shuffle = shuffle
        self.rng = np.random.default_rng(seed)

        self.source_blocks = []

        self.cumulative_counts = []

        cumulative = 0

        for item in metadata:

            count = (
                (
                    item["last_end"]
                    -
                    item["first_end"]
                )
                //
                item["stride"]
            ) + 1

            self.source_blocks.append(
                {
                    "source": item["source"],
                    "start": item["start"],
                    "end": item["end"],
                    "first_end": item["first_end"],
                    "last_end": item["last_end"],
                    "stride": item["stride"],
                    "count": count,
                }
            )

            cumulative += count

            self.cumulative_counts.append(
                cumulative
            )

        self.total_samples = cumulative

        self.indices = np.arange(
            self.total_samples,
            dtype=np.int64
        )

        self.on_epoch_end()


    def __len__(self):

        return int(
            np.ceil(
                self.total_samples
                /
                self.batch_size
            )
        )


    def on_epoch_end(self):

        if self.shuffle:

            self.rng.shuffle(
                self.indices
            )


    def _global_to_local(
        self,
        global_indices
    ):

        global_indices = np.asarray(
            global_indices,
            dtype=np.int64
        )

        block_ids = np.searchsorted(
            self.cumulative_counts,
            global_indices,
            side="right"
        )

        previous_cumulative = np.zeros(
            len(global_indices),
            dtype=np.int64
        )

        mask = block_ids > 0

        previous_cumulative[mask] = np.asarray(
            self.cumulative_counts,
            dtype=np.int64
        )[block_ids[mask] - 1]

        local_indices = (
            global_indices
            -
            previous_cumulative
        )

        return (
            block_ids,
            local_indices
        )


    def __getitem__(
        self,
        batch_index
    ):

        start_index = (
            batch_index
            *
            self.batch_size
        )

        end_index = min(
            start_index
            +
            self.batch_size,
            self.total_samples
        )

        batch_global_indices = (
            self.indices[
                start_index:end_index
            ]
        )

        block_ids, local_indices = (
            self._global_to_local(
                batch_global_indices
            )
        )


        current_batch_size = (
            len(batch_global_indices)
        )


        X_batch = np.empty(
            (
                current_batch_size,
                self.sequence_length,
                self.X.shape[1],
            ),
            dtype=np.float32,
        )

        y_batch = np.empty(
            current_batch_size,
            dtype=np.int32,
        )


        # ----------------------------------------------------
        # Build each sequence.
        #
        # Each sequence is taken from one source only.
        # ----------------------------------------------------

        for i in range(
            current_batch_size
        ):

            block = self.source_blocks[
                block_ids[i]
            ]

            local_index = (
                local_indices[i]
            )

            final_position = (
                block["first_end"]
                +
                local_index
                *
                block["stride"]
            )

            sequence_start = (
                final_position
                -
                self.sequence_length
                +
                1
            )

            sequence_end = (
                final_position + 1
            )


            X_batch[i] = self.X[
                sequence_start:sequence_end
            ]

            y_batch[i] = self.y[
                final_position
            ]


        return X_batch, y_batch


# ============================================================
# CREATE GENERATORS
# ============================================================

print("\n" + "=" * 90)
print("8. CREATING MEMORY-SAFE SEQUENCE GENERATORS")
print("=" * 90)


train_generator = SequenceBatchGenerator(
    X_train_scaled,
    y_train_all,
    train_meta,
    BATCH_SIZE,
    SEQUENCE_LENGTH,
    shuffle=True,
    seed=SEED,
)


val_generator = SequenceBatchGenerator(
    X_train_scaled,
    y_train_all,
    val_meta,
    BATCH_SIZE,
    SEQUENCE_LENGTH,
    shuffle=False,
    seed=SEED,
)


test_generator = SequenceBatchGenerator(
    X_test_scaled,
    y_test_all,
    test_meta,
    BATCH_SIZE,
    SEQUENCE_LENGTH,
    shuffle=False,
    seed=SEED,
)


print(
    "Training batches:",
    len(train_generator)
)

print(
    "Validation batches:",
    len(val_generator)
)

print(
    "Test batches:",
    len(test_generator)
)


# ============================================================
# VERIFY A REAL BATCH BEFORE TRAINING
# ============================================================

print("\n" + "=" * 90)
print("9. SEQUENCE SHAPE SANITY CHECK")
print("=" * 90)


sample_X, sample_y = (
    train_generator[0]
)


print(
    "Batch X shape:",
    sample_X.shape
)

print(
    "Batch y shape:",
    sample_y.shape
)


expected_sequence_shape = (
    SEQUENCE_LENGTH,
    69
)


if sample_X.shape[1:] != (
    SEQUENCE_LENGTH,
    69
):

    raise RuntimeError(
        "Incorrect CNN-LSTM input shape: "
        f"{sample_X.shape}"
    )


unique_batch_labels = np.unique(
    sample_y
)


print(
    "Labels in sample batch:",
    unique_batch_labels
)


print(
    "PASS: Input shape is "
    f"(batch, {SEQUENCE_LENGTH}, 69)."
)


# ============================================================
# CALCULATE CLASS WEIGHTS
# ============================================================

print("\n" + "=" * 90)
print("10. SEQUENCE CLASS BALANCING")
print("=" * 90)


def count_sequence_labels(
    generator
):

    benign = 0
    attack = 0

    for batch_index in range(
        len(generator)
    ):

        _, labels = generator[
            batch_index
        ]

        benign += int(
            np.sum(labels == 0)
        )

        attack += int(
            np.sum(labels == 1)
        )

    return benign, attack


train_sequence_benign, train_sequence_attack = (
    count_sequence_labels(
        train_generator
    )
)


val_sequence_benign, val_sequence_attack = (
    count_sequence_labels(
        val_generator
    )
)


print(
    "Training sequence BENIGN:",
    train_sequence_benign
)

print(
    "Training sequence ATTACK:",
    train_sequence_attack
)


print(
    "\nValidation sequence BENIGN:",
    val_sequence_benign
)

print(
    "Validation sequence ATTACK:",
    val_sequence_attack
)


if train_sequence_attack == 0:

    raise RuntimeError(
        "Training sequences contain zero ATTACK samples."
    )


if train_sequence_benign == 0:

    raise RuntimeError(
        "Training sequences contain zero BENIGN samples."
    )


attack_weight = (
    train_sequence_benign
    /
    train_sequence_attack
)


class_weights = {
    0: 1.0,
    1: float(attack_weight),
}


print(
    "\nClass weights:",
    class_weights
)


# ============================================================
# BUILD CNN-LSTM MODEL
# ============================================================

print("\n" + "=" * 90)
print("11. BUILDING CNN-LSTM ARCHITECTURE")
print("=" * 90)


model = Sequential(

    [

        Input(
            shape=(
                SEQUENCE_LENGTH,
                69
            )
        ),


        # ====================================================
        # CNN FEATURE EXTRACTION
        # ====================================================

        Conv1D(
            filters=32,
            kernel_size=3,
            activation="relu",
            padding="same",
        ),

        BatchNormalization(),


        Conv1D(
            filters=64,
            kernel_size=3,
            activation="relu",
            padding="same",
        ),

        BatchNormalization(),


        MaxPooling1D(
            pool_size=2
        ),


        # ====================================================
        # LSTM SEQUENTIAL LEARNING
        # ====================================================

        LSTM(
            64,
            return_sequences=False,
        ),


        # ====================================================
        # CLASSIFICATION
        # ====================================================

        Dense(
            64,
            activation="relu",
        ),

        Dropout(
            0.30
        ),


        Dense(
            2,
            activation="softmax",
        ),
    ]
)


model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ],
)


model.summary()


# ============================================================
# PILOT TRAINING
# ============================================================

print("\n" + "=" * 90)
print("12. PILOT SANITY TRAINING")
print("=" * 90)

print(
    "This is a short test before full training."
)

print(
    "The purpose is to detect collapse to "
    "a single class early."
)


PILOT_BATCHES = min(
    20,
    len(train_generator)
)


class LimitedSequence(
    tf.keras.utils.Sequence
):

    def __init__(
        self,
        base_generator,
        number_of_batches,
    ):

        self.base_generator = (
            base_generator
        )

        self.number_of_batches = (
            number_of_batches
        )


    def __len__(self):

        return self.number_of_batches


    def __getitem__(
        self,
        index
    ):

        return self.base_generator[
            index
        ]


pilot_generator = LimitedSequence(
    train_generator,
    PILOT_BATCHES,
)


pilot_model = tf.keras.models.clone_model(
    model
)


pilot_model.compile(

    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),

    loss="sparse_categorical_crossentropy",

    metrics=[
        "accuracy"
    ],
)


pilot_model.fit(

    pilot_generator,

    epochs=1,

    class_weight=class_weights,

    verbose=1,
)


# ------------------------------------------------------------
# Pilot validation
# ------------------------------------------------------------

pilot_probabilities = (
    pilot_model.predict(
        val_generator,
        verbose=1,
    )
)


pilot_predictions = np.argmax(
    pilot_probabilities,
    axis=1,
)


pilot_attack_predictions = int(
    np.sum(
        pilot_predictions == 1
    )
)


pilot_benign_predictions = int(
    np.sum(
        pilot_predictions == 0
    )
)


print(
    "\nPilot BENIGN predictions:",
    pilot_benign_predictions
)

print(
    "Pilot ATTACK predictions:",
    pilot_attack_predictions
)


if pilot_attack_predictions == 0:

    del pilot_model
    gc.collect()

    raise RuntimeError(
        "\nSTOPPED BEFORE FULL TRAINING.\n\n"
        "The pilot CNN-LSTM predicted zero "
        "ATTACK samples.\n\n"
        "No multi-hour training was started."
    )


if pilot_benign_predictions == 0:

    del pilot_model
    gc.collect()

    raise RuntimeError(
        "\nSTOPPED BEFORE FULL TRAINING.\n\n"
        "The pilot CNN-LSTM predicted zero "
        "BENIGN samples.\n\n"
        "No multi-hour training was started."
    )


print(
    "\nPASS: Pilot predicts both classes."
)


del pilot_model
del pilot_probabilities
del pilot_predictions

gc.collect()


# ============================================================
# FINAL TRAINING
# ============================================================

print("\n" + "=" * 90)
print("13. FINAL CNN-LSTM TRAINING")
print("=" * 90)


print(
    "Training windows:",
    f"{train_window_count:,}"
)

print(
    "Validation windows:",
    f"{val_window_count:,}"
)

print(
    "Batch size:",
    BATCH_SIZE
)

print(
    "Maximum epochs:",
    EPOCHS
)


early_stopping = EarlyStopping(

    monitor="val_loss",

    patience=2,

    restore_best_weights=True,

    verbose=1,
)


reduce_lr = ReduceLROnPlateau(

    monitor="val_loss",

    factor=0.5,

    patience=1,

    min_lr=1e-6,

    verbose=1,
)


start_time = time.time()


history = model.fit(

    train_generator,

    validation_data=val_generator,

    epochs=EPOCHS,

    class_weight=class_weights,

    callbacks=[
        early_stopping,
        reduce_lr,
    ],

    verbose=1,
)


training_time = (
    time.time()
    -
    start_time
)


print(
    "\nTraining time:",
    round(
        training_time,
        2
    ),
    "seconds"
)


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

print("\n" + "=" * 90)
print("14. VALIDATION PREDICTIONS")
print("=" * 90)


val_probabilities = (
    model.predict(
        val_generator,
        verbose=1,
    )
)


val_true = []
val_attack_probability = []


for batch_index in range(
    len(val_generator)
):

    _, batch_labels = (
        val_generator[
            batch_index
        ]
    )

    batch_probabilities = (
        val_probabilities[
            batch_index
            *
            BATCH_SIZE:
            min(
                (
                    batch_index + 1
                )
                *
                BATCH_SIZE,
                len(val_probabilities),
            )
        ]
    )

    val_true.extend(
        batch_labels.tolist()
    )

    val_attack_probability.extend(
        batch_probabilities[:, 1]
        .tolist()
    )


val_true = np.asarray(
    val_true,
    dtype=np.int32,
)

val_attack_probability = np.asarray(
    val_attack_probability,
    dtype=np.float32,
)


# ============================================================
# THRESHOLD SELECTION
# ============================================================

print("\n" + "=" * 90)
print("15. VALIDATION THRESHOLD SELECTION")
print("=" * 90)


best_threshold = 0.50
best_validation_f1 = -1.0


for threshold in np.arange(
    0.10,
    0.91,
    0.01,
):

    validation_predictions = (
        val_attack_probability
        >= threshold
    ).astype(np.int32)


    current_f1 = f1_score(
        val_true,
        validation_predictions,
        zero_division=0,
    )


    if current_f1 > best_validation_f1:

        best_validation_f1 = (
            current_f1
        )

        best_threshold = float(
            threshold
        )


print(
    "Selected threshold:",
    best_threshold
)

print(
    "Validation F1:",
    best_validation_f1
)


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

print("\n" + "=" * 90)
print("16. FINAL UNSEEN TEST EVALUATION")
print("=" * 90)


test_probabilities = (
    model.predict(
        test_generator,
        verbose=1,
    )
)


test_true = []
test_attack_probability = []


for batch_index in range(
    len(test_generator)
):

    _, batch_labels = (
        test_generator[
            batch_index
        ]
    )

    start = (
        batch_index
        *
        BATCH_SIZE
    )

    end = min(
        (
            batch_index + 1
        )
        *
        BATCH_SIZE,
        len(test_probabilities),
    )


    batch_probabilities = (
        test_probabilities[
            start:end
        ]
    )


    test_true.extend(
        batch_labels.tolist()
    )

    test_attack_probability.extend(
        batch_probabilities[:, 1]
        .tolist()
    )


test_true = np.asarray(
    test_true,
    dtype=np.int32,
)

test_attack_probability = np.asarray(
    test_attack_probability,
    dtype=np.float32,
)


# ============================================================
# FINAL CLASSIFICATION
# ============================================================

test_predictions = (
    test_attack_probability
    >= best_threshold
).astype(np.int32)


# ============================================================
# PREDICTION DISTRIBUTION
# ============================================================

test_pred_benign = int(
    np.sum(
        test_predictions == 0
    )
)

test_pred_attack = int(
    np.sum(
        test_predictions == 1
    )
)


print(
    "\nTest predictions:"
)

print(
    "BENIGN:",
    test_pred_benign
)

print(
    "ATTACK:",
    test_pred_attack
)


if test_pred_attack == 0:

    print(
        "\nWARNING:"
    )

    print(
        "CNN-LSTM predicted no ATTACK "
        "samples at the selected threshold."
    )


# ============================================================
# METRICS
# ============================================================

accuracy = accuracy_score(
    test_true,
    test_predictions,
)


precision = precision_score(
    test_true,
    test_predictions,
    zero_division=0,
)


recall = recall_score(
    test_true,
    test_predictions,
    zero_division=0,
)


f1 = f1_score(
    test_true,
    test_predictions,
    zero_division=0,
)


roc_auc = roc_auc_score(
    test_true,
    test_attack_probability,
)


pr_auc = average_precision_score(
    test_true,
    test_attack_probability,
)


cm = confusion_matrix(
    test_true,
    test_predictions,
)


# ============================================================
# FINAL RESULTS
# ============================================================

print("\n" + "=" * 90)
print("FINAL CNN-LSTM RESULTS")
print("=" * 90)


print(
    f"Accuracy  : {accuracy:.6f}"
)

print(
    f"Precision : {precision:.6f}"
)

print(
    f"Recall    : {recall:.6f}"
)

print(
    f"F1        : {f1:.6f}"
)

print(
    f"ROC-AUC   : {roc_auc:.6f}"
)

print(
    f"PR-AUC    : {pr_auc:.6f}"
)

print(
    f"Threshold : {best_threshold:.2f}"
)

print(
    f"Training Time : {training_time:.2f} seconds"
)


print(
    "\nConfusion Matrix:"
)

print(cm)


# ============================================================
# SAVE MODEL
# ============================================================

print("\n" + "=" * 90)
print("17. SAVING RESULTS")
print("=" * 90)


model.save(
    MODEL_PATH
)


print(
    "Model saved:",
    MODEL_PATH
)


# ============================================================
# SAVE METRICS
# ============================================================

results_df = pd.DataFrame(
    [
        {
            "Model":
                "CNN-LSTM",

            "Evaluation":
                "Final Group-Aware",

            "Accuracy":
                accuracy,

            "Precision":
                precision,

            "Recall":
                recall,

            "F1":
                f1,

            "ROC_AUC":
                roc_auc,

            "PR_AUC":
                pr_auc,

            "Threshold":
                best_threshold,

            "Training_Time_Seconds":
                training_time,

            "Sequence_Length":
                SEQUENCE_LENGTH,

            "Train_Stride":
                TRAIN_STRIDE,

            "Validation_Stride":
                VAL_STRIDE,

            "Test_Stride":
                TEST_STRIDE,
        }
    ]
)


results_df.to_csv(
    METRICS_PATH,
    index=False,
)


print(
    "Metrics saved:",
    METRICS_PATH
)


# ============================================================
# CLEANUP
# ============================================================

del train_generator
del val_generator
del test_generator

gc.collect()


print("\n" + "=" * 90)
print("CNN-LSTM EXPERIMENT COMPLETE")
print("=" * 90)