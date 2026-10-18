from pathlib import Path
import pandas as pd

DATASET_DIR = Path("dataset")


def main():

    files = sorted(DATASET_DIR.glob("*.parquet"))

    print("=" * 80)
    print("SECURESENSE - BINARY LABEL CONFLICT ANALYSIS")
    print("=" * 80)

    frames = []

    for file in files:

        print(f"Loading: {file.name}")

        df = pd.read_parquet(file)

        df["source_file"] = file.name

        frames.append(df)

    print("\nCombining datasets...")

    data = pd.concat(frames, ignore_index=True)

    feature_columns = [
        column
        for column in data.columns
        if column not in ["Label", "source_file"]
    ]

    # ---------------------------------------------------------
    # Create binary target
    # ---------------------------------------------------------

    data["BinaryLabel"] = (
        data["Label"]
        .astype(str)
        .str.strip()
        .str.lower()
        .apply(
            lambda x: "BENIGN"
            if x == "benign"
            else "ATTACK"
        )
    )

    # ---------------------------------------------------------
    # Find feature groups with more than one original label
    # ---------------------------------------------------------

    print("\nFinding feature groups with multiple original labels...")

    label_counts = (
        data.groupby(feature_columns, dropna=False)["Label"]
        .nunique()
    )

    original_conflicts = label_counts[
        label_counts > 1
    ]

    print(
        f"\nOriginal-label conflict groups: "
        f"{len(original_conflicts):,}"
    )

    # ---------------------------------------------------------
    # Find feature groups with more than one binary label
    # ---------------------------------------------------------

    print("\nChecking binary-label conflicts...")

    binary_counts = (
        data.groupby(feature_columns, dropna=False)["BinaryLabel"]
        .nunique()
    )

    binary_conflicts = binary_counts[
        binary_counts > 1
    ]

    print(
        f"Binary-label conflict groups: "
        f"{len(binary_conflicts):,}"
    )

    # ---------------------------------------------------------
    # Rows affected by binary conflicts
    # ---------------------------------------------------------

    if len(binary_conflicts) > 0:

        conflict_index = binary_conflicts.index

        conflict_rows = (
            data.set_index(feature_columns)
            .loc[conflict_index]
            .reset_index()
        )

        print(
            f"Rows belonging to binary-conflict groups: "
            f"{len(conflict_rows):,}"
        )

        print("\nBinary conflict label distribution:")

        print(
            conflict_rows["BinaryLabel"]
            .value_counts()
        )

        print("\nOriginal labels involved:")

        print(
            conflict_rows["Label"]
            .value_counts()
        )

        print("\nSources involved:")

        print(
            conflict_rows["source_file"]
            .value_counts()
        )

    else:

        print(
            "SUCCESS: No feature groups have "
            "both BENIGN and ATTACK labels."
        )

    # ---------------------------------------------------------
    # Compare exact duplicate groups
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("EXACT DUPLICATE GROUPS")
    print("=" * 80)

    exact_duplicate_groups = (
        data.groupby(
            feature_columns + ["Label"],
            dropna=False
        )
        .size()
    )

    exact_duplicate_groups = exact_duplicate_groups[
        exact_duplicate_groups > 1
    ]

    print(
        f"Exact duplicate groups: "
        f"{len(exact_duplicate_groups):,}"
    )

    # ---------------------------------------------------------
    # Constant features
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("CONSTANT FEATURES")
    print("=" * 80)

    constant_features = []

    for column in feature_columns:

        if data[column].nunique(dropna=False) <= 1:
            constant_features.append(column)

    for column in constant_features:
        print(" -", column)

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"Total rows: {len(data):,}")
    print(
        f"Original-label conflict groups: "
        f"{len(original_conflicts):,}"
    )
    print(
        f"Binary-label conflict groups: "
        f"{len(binary_conflicts):,}"
    )
    print(
        f"Constant features: "
        f"{len(constant_features)}"
    )

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()