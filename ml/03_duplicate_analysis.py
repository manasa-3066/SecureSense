from pathlib import Path
import pandas as pd
import numpy as np

DATASET_DIR = Path("dataset")


def main():

    files = sorted(DATASET_DIR.glob("*.parquet"))

    print("=" * 80)
    print("SECURESENSE - DUPLICATE AND LABEL CONFLICT ANALYSIS")
    print("=" * 80)

    frames = []

    for file in files:

        print(f"Loading: {file.name}")

        df = pd.read_parquet(file)

        df["source_file"] = file.name

        frames.append(df)

    print("\nCombining datasets...")

    data = pd.concat(frames, ignore_index=True)

    print(f"Total rows: {len(data):,}")

    # ---------------------------------------------------------
    # Separate feature columns from metadata
    # ---------------------------------------------------------

    feature_columns = [
        col for col in data.columns
        if col not in ["Label", "source_file"]
    ]

    print(f"Feature columns: {len(feature_columns)}")

    # ---------------------------------------------------------
    # 1. Exact duplicate check including label
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("1. EXACT DUPLICATES INCLUDING LABEL")
    print("=" * 80)

    duplicate_mask = data.duplicated(
        subset=feature_columns + ["Label"],
        keep=False
    )

    duplicate_rows = data[duplicate_mask]

    print(
        f"Rows belonging to exact duplicate groups: "
        f"{len(duplicate_rows):,}"
    )

    # Number of duplicate occurrences excluding first
    duplicate_occurrences = data.duplicated(
        subset=feature_columns + ["Label"],
        keep="first"
    ).sum()

    print(
        f"Duplicate occurrences excluding first: "
        f"{duplicate_occurrences:,}"
    )

    # ---------------------------------------------------------
    # 2. Duplicate distribution by label
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("2. DUPLICATES BY LABEL")
    print("=" * 80)

    if len(duplicate_rows) > 0:

        duplicate_by_label = (
            duplicate_rows["Label"]
            .value_counts()
        )

        print(duplicate_by_label)

    else:

        print("No duplicates found.")

    # ---------------------------------------------------------
    # 3. Duplicate distribution by source file
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("3. DUPLICATES BY SOURCE FILE")
    print("=" * 80)

    if len(duplicate_rows) > 0:

        print(
            duplicate_rows["source_file"]
            .value_counts()
        )

    # ---------------------------------------------------------
    # 4. Feature-only duplicate check
    #    Label is intentionally excluded.
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("4. FEATURE-ONLY DUPLICATE ANALYSIS")
    print("=" * 80)

    feature_duplicate_mask = data.duplicated(
        subset=feature_columns,
        keep=False
    )

    feature_duplicates = data[feature_duplicate_mask]

    print(
        f"Rows belonging to feature-duplicate groups: "
        f"{len(feature_duplicates):,}"
    )

    # ---------------------------------------------------------
    # 5. Check for conflicting labels
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("5. LABEL CONFLICT CHECK")
    print("=" * 80)

    if len(feature_duplicates) == 0:

        print("No feature duplicates found.")

    else:

        label_counts_per_feature = (
            feature_duplicates
            .groupby(feature_columns, dropna=False)["Label"]
            .nunique()
        )

        conflicting_groups = (
            label_counts_per_feature[
                label_counts_per_feature > 1
            ]
        )

        print(
            f"Feature groups with multiple labels: "
            f"{len(conflicting_groups):,}"
        )

        if len(conflicting_groups) > 0:

            print("\nWARNING: Label conflicts detected.")

            print("\nExample conflicting records:")

            conflict_features = (
                conflicting_groups
                .head(10)
                .index
            )

            examples = (
                feature_duplicates
                .set_index(feature_columns)
                .loc[conflict_features]
                .reset_index()
            )

            print(examples[feature_columns + ["Label", "source_file"]])

        else:

            print(
                "SUCCESS: No identical feature vectors "
                "were found with different labels."
            )

    # ---------------------------------------------------------
    # 6. Cross-file duplicate pairs
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("6. CROSS-FILE DUPLICATE CHECK")
    print("=" * 80)

    if len(duplicate_rows) > 0:

        source_counts = (
            duplicate_rows
            .groupby(feature_columns + ["Label"])["source_file"]
            .nunique()
        )

        cross_file_groups = source_counts[
            source_counts > 1
        ]

        print(
            f"Duplicate groups appearing in multiple files: "
            f"{len(cross_file_groups):,}"
        )

    # ---------------------------------------------------------
    # 7. Constant columns
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("7. CONSTANT FEATURES")
    print("=" * 80)

    constant_columns = []

    for column in feature_columns:

        unique_count = data[column].nunique(
            dropna=False
        )

        if unique_count <= 1:
            constant_columns.append(column)

    if constant_columns:

        print("Constant columns:")

        for column in constant_columns:
            print(f" - {column}")

    else:

        print("No constant columns found.")

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()