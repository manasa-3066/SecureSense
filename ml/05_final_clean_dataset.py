import os
import pandas as pd
import numpy as np

# ============================================================
# SECURESENSE - FINAL DATASET CLEANING
# ============================================================

DATA_DIR = "dataset"
OUTPUT_DIR = "data/cleaned"

os.makedirs(OUTPUT_DIR, exist_ok=True)

FILES = [
    "Benign-Monday-no-metadata.parquet",
    "Botnet-Friday-no-metadata.parquet",
    "Bruteforce-Tuesday-no-metadata.parquet",
    "DDoS-Friday-no-metadata.parquet",
    "DoS-Wednesday-no-metadata.parquet",
    "Infiltration-Thursday-no-metadata.parquet",
    "Portscan-Friday-no-metadata.parquet",
    "WebAttacks-Thursday-no-metadata.parquet",
]

CONSTANT_FEATURES = [
    "Bwd PSH Flags",
    "Bwd URG Flags",
    "Fwd Avg Bytes/Bulk",
    "Fwd Avg Packets/Bulk",
    "Fwd Avg Bulk Rate",
    "Bwd Avg Bytes/Bulk",
    "Bwd Avg Packets/Bulk",
    "Bwd Avg Bulk Rate",
]

LABEL_COLUMN = "Label"


def main():

    print("=" * 80)
    print("SECURESENSE - FINAL DATASET CLEANING")
    print("=" * 80)

    # --------------------------------------------------------
    # 1. LOAD DATA
    # --------------------------------------------------------

    frames = []

    for filename in FILES:
        path = os.path.join(DATA_DIR, filename)

        print(f"Loading: {filename}")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Dataset not found: {path}")

        df = pd.read_parquet(path)

        # Keep source information for auditing
        df["_source_file"] = filename

        frames.append(df)

    print("\nCombining datasets...")

    df = pd.concat(frames, ignore_index=True)

    print(f"Raw rows: {len(df):,}")
    print(f"Raw columns: {len(df.columns):,}")

    # --------------------------------------------------------
    # 2. NORMALIZE LABELS
    # --------------------------------------------------------

    if LABEL_COLUMN not in df.columns:
        raise ValueError("Label column not found.")

    df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(str).str.strip()

    df["BinaryLabel"] = np.where(
        df[LABEL_COLUMN].str.upper() == "BENIGN",
        "BENIGN",
        "ATTACK"
    )

    # --------------------------------------------------------
    # 3. REMOVE MISSING / INFINITE VALUES
    # --------------------------------------------------------

    print("\nChecking missing and infinite values...")

    feature_columns = [
        c for c in df.columns
        if c not in [LABEL_COLUMN, "BinaryLabel", "_source_file"]
    ]

    numeric_columns = df[feature_columns].select_dtypes(
        include=[np.number]
    ).columns

    missing_before = int(df[numeric_columns].isna().sum().sum())

    infinite_before = int(
        np.isinf(df[numeric_columns].to_numpy()).sum()
    )

    print(f"Missing numeric values: {missing_before:,}")
    print(f"Infinite numeric values: {infinite_before:,}")

    if missing_before > 0 or infinite_before > 0:
        df[numeric_columns] = df[numeric_columns].replace(
            [np.inf, -np.inf], np.nan
        )

        before = len(df)

        df = df.dropna(subset=numeric_columns).reset_index(drop=True)

        print(
            f"Rows removed because of missing/infinite values: "
            f"{before - len(df):,}"
        )

    # --------------------------------------------------------
    # 4. REMOVE CONSTANT FEATURES
    # --------------------------------------------------------

    print("\nRemoving constant features...")

    existing_constant_features = [
        c for c in CONSTANT_FEATURES
        if c in df.columns
    ]

    df = df.drop(columns=existing_constant_features)

    print(
        f"Constant features removed: "
        f"{len(existing_constant_features)}"
    )

    for feature in existing_constant_features:
        print(f"  - {feature}")

    # --------------------------------------------------------
    # 5. IDENTIFY CONFLICTING FEATURE GROUPS
    # --------------------------------------------------------

    print("\nFinding conflicting feature groups...")

    feature_columns = [
        c for c in df.columns
        if c not in [LABEL_COLUMN, "BinaryLabel", "_source_file"]
    ]

    # A feature group is identified by all model input features.
    #
    # If the same feature vector occurs with both BENIGN and ATTACK,
    # it is ambiguous and will be removed completely.

    label_counts = (
        df.groupby(feature_columns, dropna=False)["BinaryLabel"]
        .nunique()
        .reset_index(name="label_count")
    )

    conflicting_groups = label_counts[
        label_counts["label_count"] > 1
    ]

    print(
        f"Conflicting feature groups: "
        f"{len(conflicting_groups):,}"
    )

    # --------------------------------------------------------
    # 6. REMOVE ALL ROWS BELONGING TO CONFLICTING GROUPS
    # --------------------------------------------------------

    if len(conflicting_groups) > 0:

        conflict_index = pd.MultiIndex.from_frame(
            conflicting_groups[feature_columns]
        )

        row_index = pd.MultiIndex.from_frame(
            df[feature_columns]
        )

        conflict_mask = row_index.isin(conflict_index)

        conflicting_rows = int(conflict_mask.sum())

        print(
            f"Rows removed because of conflicting labels: "
            f"{conflicting_rows:,}"
        )

        df = df.loc[~conflict_mask].reset_index(drop=True)

    else:
        print("No conflicting groups found.")

    # --------------------------------------------------------
    # 7. CHECK FOR EXACT DUPLICATE FEATURE VECTORS
    # --------------------------------------------------------

    print("\nChecking exact duplicate feature vectors...")

    duplicate_mask = df.duplicated(
        subset=feature_columns,
        keep=False
    )

    duplicate_rows = int(duplicate_mask.sum())

    duplicate_groups = int(
        df.loc[duplicate_mask, feature_columns]
        .drop_duplicates()
        .shape[0]
    )

    print(f"Duplicate feature-vector groups: {duplicate_groups:,}")
    print(f"Rows belonging to duplicate groups: {duplicate_rows:,}")

    # --------------------------------------------------------
    # 8. REMOVE EXACT DUPLICATES
    # --------------------------------------------------------

    #
    # IMPORTANT:
    #
    # We retain only one copy of each identical feature vector.
    #
    # Since conflicting feature groups were removed already,
    # every remaining identical feature vector has one binary label.
    #

    before_duplicates = len(df)

    df = df.drop_duplicates(
        subset=feature_columns,
        keep="first"
    ).reset_index(drop=True)

    removed_duplicates = before_duplicates - len(df)

    print(
        f"Duplicate rows removed: "
        f"{removed_duplicates:,}"
    )

    # --------------------------------------------------------
    # 9. FINAL VALIDATION
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("FINAL DATASET VALIDATION")
    print("=" * 80)

    print(f"Final rows: {len(df):,}")
    print(f"Final columns: {len(df.columns):,}")
    print(f"Final model features: {len(feature_columns):,}")

    print("\nBinary class distribution:")

    class_distribution = (
        df["BinaryLabel"]
        .value_counts()
    )

    print(class_distribution)

    print("\nBinary class percentages:")

    class_percentages = (
        df["BinaryLabel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(4)
    )

    print(class_percentages)

    # --------------------------------------------------------
    # 10. FINAL SAFETY CHECKS
    # --------------------------------------------------------

    print("\nSafety checks:")

    # Missing
    missing_final = int(
        df[feature_columns]
        .isna()
        .sum()
        .sum()
    )

    # Infinite
    infinite_final = int(
        np.isinf(
            df[feature_columns]
            .select_dtypes(include=[np.number])
            .to_numpy()
        ).sum()
    )

    # Duplicate feature vectors
    remaining_duplicates = int(
        df.duplicated(
            subset=feature_columns,
            keep=False
        ).sum()
    )

    # Conflicting binary labels
    remaining_conflicts = int(
        (
            df.groupby(feature_columns, dropna=False)["BinaryLabel"]
            .nunique() > 1
        ).sum()
    )

    print(f"Missing values:              {missing_final:,}")
    print(f"Infinite values:             {infinite_final:,}")
    print(f"Remaining duplicate rows:   {remaining_duplicates:,}")
    print(f"Remaining conflict groups:  {remaining_conflicts:,}")

    # --------------------------------------------------------
    # 11. HARD VALIDATION
    # --------------------------------------------------------

    if missing_final != 0:
        raise RuntimeError("FAILED: Missing values remain.")

    if infinite_final != 0:
        raise RuntimeError("FAILED: Infinite values remain.")

    if remaining_duplicates != 0:
        raise RuntimeError(
            "FAILED: Duplicate feature vectors remain."
        )

    if remaining_conflicts != 0:
        raise RuntimeError(
            "FAILED: Conflicting binary labels remain."
        )

    # --------------------------------------------------------
    # 12. SAVE FINAL DATASET
    # --------------------------------------------------------

    output_path = os.path.join(
        OUTPUT_DIR,
        "securesense_final_binary.parquet"
    )

    df.to_parquet(
        output_path,
        index=False
    )

    print("\n" + "=" * 80)
    print("DATASET CLEANING SUCCESSFUL")
    print("=" * 80)

    print(f"Saved to:")
    print(output_path)

    print("\nALL SAFETY CHECKS PASSED.")
    print("=" * 80)


if __name__ == "__main__":
    main()