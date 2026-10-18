import pandas as pd

DATA_PATH = "data/cleaned/securesense_final_binary.parquet"

print("=" * 80)
print("SECURESENSE - FINAL SPLIT AUDIT")
print("=" * 80)

df = pd.read_parquet(DATA_PATH)

print(f"\nTotal rows: {len(df):,}")

print("\nRows by source file and binary label:")
print(
    pd.crosstab(
        df["_source_file"],
        df["BinaryLabel"],
        margins=True
    )
)

print("\nPercentages within each source file:")

for source, group in df.groupby("_source_file"):

    counts = group["BinaryLabel"].value_counts()

    benign = int(counts.get("BENIGN", 0))
    attack = int(counts.get("ATTACK", 0))
    total = len(group)

    print("\n" + source)
    print(f"  Total:  {total:,}")
    print(f"  BENIGN: {benign:,} ({benign / total * 100:.2f}%)")
    print(f"  ATTACK: {attack:,} ({attack / total * 100:.2f}%)")

print("\n" + "=" * 80)