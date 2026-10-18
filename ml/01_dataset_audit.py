from pathlib import Path
import pandas as pd
import numpy as np

DATASET_DIR = Path("dataset")


def find_label_column(columns):
    """
    Try to identify the target/label column.
    """
    candidates = [
        "Label",
        "label",
        "LABEL",
        "Class",
        "class",
        "Target",
        "target"
    ]

    for candidate in candidates:
        if candidate in columns:
            return candidate

    return None


def main():

    files = sorted(DATASET_DIR.glob("*.parquet"))

    if not files:
        print("ERROR: No parquet files found in dataset folder.")
        return

    print("=" * 80)
    print("SECURESENSE - CICIDS2017 DATASET AUDIT")
    print("=" * 80)

    print(f"\nNumber of parquet files found: {len(files)}")

    all_schemas = {}

    for file in files:

        print("\n" + "=" * 80)
        print(f"FILE: {file.name}")
        print("=" * 80)

        # Read only the parquet file
        df = pd.read_parquet(file)

        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")

        print("\nColumns:")
        print(list(df.columns))

        # Find label
        label_col = find_label_column(df.columns)

        if label_col:
            print(f"\nLabel column: {label_col}")

            print("\nClass distribution:")
            counts = df[label_col].value_counts(dropna=False)

            percentages = (
                df[label_col]
                .value_counts(dropna=False, normalize=True)
                .mul(100)
                .round(4)
            )

            distribution = pd.DataFrame({
                "Count": counts,
                "Percentage": percentages
            })

            print(distribution)

        else:
            print("\nWARNING: Label column was not automatically detected.")

        # Missing values
        missing = df.isna().sum()

        missing = missing[missing > 0].sort_values(ascending=False)

        print("\nMissing values:")
        if len(missing) == 0:
            print("None")
        else:
            print(missing)

        # Infinite values
        numeric_df = df.select_dtypes(include=[np.number])

        if not numeric_df.empty:

            infinite_count = np.isinf(numeric_df).sum().sum()

            print(f"\nInfinite numeric values: {infinite_count:,}")

        else:
            print("\nNo numeric columns detected.")

        # Duplicate rows
        duplicate_count = df.duplicated().sum()

        print(f"\nDuplicate rows: {duplicate_count:,}")

        # Data types
        print("\nData types:")
        print(df.dtypes)

        # Store schema
        all_schemas[file.name] = list(df.columns)

        del df

    # ------------------------------------------------------------------
    # Compare schemas
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("SCHEMA CONSISTENCY CHECK")
    print("=" * 80)

    first_file = list(all_schemas.keys())[0]
    first_schema = all_schemas[first_file]

    schema_consistent = True

    for filename, schema in all_schemas.items():

        if schema != first_schema:

            schema_consistent = False

            print(f"\nSCHEMA DIFFERENCE FOUND: {filename}")

            missing_columns = set(first_schema) - set(schema)
            extra_columns = set(schema) - set(first_schema)

            if missing_columns:
                print("Missing columns:", missing_columns)

            if extra_columns:
                print("Extra columns:", extra_columns)

    if schema_consistent:
        print("\nSUCCESS: All files have the same column order and schema.")

    print("\n" + "=" * 80)
    print("AUDIT COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()