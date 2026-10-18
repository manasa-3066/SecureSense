from pathlib import Path
import pandas as pd
import numpy as np

DATASET_DIR = Path("dataset")


def main():

    files = sorted(DATASET_DIR.glob("*.parquet"))

    print("=" * 80)
    print("SECURESENSE - GLOBAL DATASET AUDIT")
    print("=" * 80)

    frames = []

    for file in files:

        print(f"\nLoading: {file.name}")

        df = pd.read_parquet(file)

        # Add source information for auditing
        df["source_file"] = file.name

        frames.append(df)

    print("\nCombining datasets...")

    data = pd.concat(frames, ignore_index=True)

    print("\n" + "=" * 80)
    print("GLOBAL DATASET")
    print("=" * 80)

    print(f"Total rows    : {len(data):,}")
    print(f"Total columns : {len(data.columns):,}")

    # ---------------------------------------------------------
    # Label distribution
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("GLOBAL LABEL DISTRIBUTION")
    print("=" * 80)

    label_counts = data["Label"].value_counts(dropna=False)

    label_percentages = (
        data["Label"]
        .value_counts(normalize=True, dropna=False)
        .mul(100)
        .round(4)
    )

    distribution = pd.DataFrame({
        "Count": label_counts,
        "Percentage": label_percentages
    })

    print(distribution)

    # ---------------------------------------------------------
    # Binary attack distribution
    # ---------------------------------------------------------

    data["BinaryLabel"] = (
        data["Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .apply(lambda x: 0 if x == "benign" else 1)
    )

    print("\n" + "=" * 80)
    print("BINARY LABEL DISTRIBUTION")
    print("=" * 80)

    binary_counts = data["BinaryLabel"].value_counts()

    binary_percentages = (
        data["BinaryLabel"]
        .value_counts(normalize=True)
        .mul(100)
        .round(4)
    )

    binary_distribution = pd.DataFrame({
        "Count": binary_counts,
        "Percentage": binary_percentages
    })

    binary_distribution.index = ["ATTACK" if i == 1 else "BENIGN"
                                 for i in binary_distribution.index]

    print(binary_distribution)

    # ---------------------------------------------------------
    # Cross-file duplicates
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("CROSS-FILE DUPLICATE CHECK")
    print("=" * 80)

    # Remove audit-only columns
    feature_columns = [
        col for col in data.columns
        if col not in ["source_file", "BinaryLabel"]
    ]

    duplicate_count = data.duplicated(
        subset=feature_columns
    ).sum()

    print(f"Duplicate records across all files: {duplicate_count:,}")

    # ---------------------------------------------------------
    # Constant columns
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("CONSTANT COLUMN CHECK")
    print("=" * 80)

    constant_columns = []

    for column in feature_columns:

        if data[column].nunique(dropna=False) <= 1:
            constant_columns.append(column)

    if constant_columns:
        print("Constant columns:")
        for column in constant_columns:
            print(" -", column)
    else:
        print("No constant columns found.")

    # ---------------------------------------------------------
    # Source file distribution
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("SOURCE FILE DISTRIBUTION")
    print("=" * 80)

    print(data["source_file"].value_counts())

    # ---------------------------------------------------------
    # Label vs source file
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("LABEL DISTRIBUTION BY SOURCE FILE")
    print("=" * 80)

    cross_tab = pd.crosstab(
        data["source_file"],
        data["Label"]
    )

    print(cross_tab)

    print("\n" + "=" * 80)
    print("GLOBAL AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()