import joblib
import pandas as pd
from pathlib import Path


# ============================================================
# SECURESENSE - CREATE 10-ROW DEMO FILE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "cleaned"
    / "securesense_final_binary.parquet"
)

MODEL_PATH = (
    BASE_DIR
    / "models"
    / "final_random_forest.pkl"
)

FEATURES_PATH = (
    BASE_DIR
    / "models"
    / "final_feature_names.pkl"
)

OUTPUT_DIR = BASE_DIR / "results" / "demo"


# ------------------------------------------------------------
# Create output directory
# ------------------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


print("=" * 70)
print("SECURESENSE - 10 ROW DEMO GENERATOR")
print("=" * 70)

print()
print("Loading model...")
model = joblib.load(MODEL_PATH)

print("Loading feature names...")
feature_names = joblib.load(FEATURES_PATH)

print(f"Number of model features: {len(feature_names)}")

print()
print("Loading cleaned dataset...")
df = pd.read_parquet(DATA_PATH)

print(f"Dataset rows: {len(df):,}")
print(f"Dataset columns: {len(df.columns)}")


# ------------------------------------------------------------
# Find label column
# ------------------------------------------------------------

label_candidates = [
    "Label",
    "label",
    "Target",
    "target",
    "Class",
    "class",
]

label_column = None

for column in label_candidates:
    if column in df.columns:
        label_column = column
        break

if label_column is None:
    raise RuntimeError(
        "Could not find the label column. "
        "Expected one of: "
        + ", ".join(label_candidates)
    )

print(f"Label column: {label_column}")


# ------------------------------------------------------------
# Check required model features
# ------------------------------------------------------------

missing_features = [
    feature
    for feature in feature_names
    if feature not in df.columns
]

if missing_features:
    raise RuntimeError(
        f"Missing {len(missing_features)} model features.\n"
        f"First missing features: {missing_features[:10]}"
    )

print("All 69 model features are present.")


# ------------------------------------------------------------
# Prepare model input
# ------------------------------------------------------------

X = df[feature_names].copy()


# ------------------------------------------------------------
# Predict in chunks
# ------------------------------------------------------------

print()
print("Running Random Forest predictions...")
print("This may take a few minutes because the dataset is large.")
print()

chunk_size = 50000

selected = {
    "BENIGN": [],
    "MEDIUM": [],
    "HIGH": [],
    "CRITICAL": [],
}

total_rows = len(df)

for start in range(0, total_rows, chunk_size):

    end = min(start + chunk_size, total_rows)

    X_chunk = X.iloc[start:end]

    probabilities = model.predict_proba(X_chunk)

    predictions = model.classes_[probabilities.argmax(axis=1)]

    confidences = probabilities.max(axis=1)

    for local_index, (prediction, confidence) in enumerate(
        zip(predictions, confidences)
    ):

        global_index = start + local_index

        # Convert model prediction to string
        prediction_text = str(prediction).upper()

        # ----------------------------------------------------
        # BENIGN
        # ----------------------------------------------------

        if prediction_text == "BENIGN" or prediction == 0:

            if len(selected["BENIGN"]) < 2:

                selected["BENIGN"].append(
                    {
                        "index": global_index,
                        "prediction": "BENIGN",
                        "confidence": float(confidence),
                        "risk": "LOW",
                    }
                )

        # ----------------------------------------------------
        # ATTACK
        # ----------------------------------------------------

        else:

            confidence = float(confidence)

            if confidence >= 0.90:
                risk = "CRITICAL"

            elif confidence >= 0.75:
                risk = "HIGH"

            elif confidence >= 0.50:
                risk = "MEDIUM"

            else:
                risk = "LOW"

            if risk in selected:

                if len(selected[risk]) < 2:

                    selected[risk].append(
                        {
                            "index": global_index,
                            "prediction": "ATTACK",
                            "confidence": confidence,
                            "risk": risk,
                        }
                    )

    found_counts = {
        key: len(value)
        for key, value in selected.items()
    }

    print(
        f"Processed {end:,}/{total_rows:,} rows | "
        f"Found: {found_counts}"
    )

    # Stop once we have:
    # 2 BENIGN
    # 2 MEDIUM
    # 2 HIGH
    # 2 CRITICAL
    #
    # The remaining 2 rows will be additional attack examples.

    if (
        len(selected["BENIGN"]) >= 2
        and len(selected["MEDIUM"]) >= 2
        and len(selected["HIGH"]) >= 2
        and len(selected["CRITICAL"]) >= 2
    ):
        break


# ------------------------------------------------------------
# Verify required categories
# ------------------------------------------------------------

print()
print("=" * 70)
print("SELECTION SUMMARY")
print("=" * 70)

for category in ["BENIGN", "MEDIUM", "HIGH", "CRITICAL"]:
    print(
        f"{category:10s}: "
        f"{len(selected[category])} records"
    )


required_categories = [
    "BENIGN",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
]

missing_categories = [
    category
    for category in required_categories
    if len(selected[category]) < 2
]

if missing_categories:

    raise RuntimeError(
        "\nCould not find two records for: "
        + ", ".join(missing_categories)
        + "\n\n"
        "No output file was created. "
        "Do NOT modify the model or dataset."
    )


# ------------------------------------------------------------
# Build 10-row selection
# ------------------------------------------------------------

chosen = []

# 2 BENIGN
chosen.extend(selected["BENIGN"][:2])

# 2 MEDIUM
chosen.extend(selected["MEDIUM"][:2])

# 2 HIGH
chosen.extend(selected["HIGH"][:2])

# 2 CRITICAL
chosen.extend(selected["CRITICAL"][:2])


# ------------------------------------------------------------
# Add 2 additional attack examples
# ------------------------------------------------------------

additional_attacks = []

for category in ["CRITICAL", "HIGH", "MEDIUM"]:

    for item in selected[category][2:]:

        additional_attacks.append(item)

        if len(additional_attacks) == 2:
            break

    if len(additional_attacks) == 2:
        break


# If not enough additional records were stored,
# use more records from existing categories.
if len(additional_attacks) < 2:

    for category in ["CRITICAL", "HIGH", "MEDIUM"]:

        for item in selected[category]:

            if item not in chosen:
                additional_attacks.append(item)

            if len(additional_attacks) == 2:
                break

        if len(additional_attacks) == 2:
            break


chosen.extend(additional_attacks[:2])


# ------------------------------------------------------------
# Remove accidental duplicates
# ------------------------------------------------------------

unique_chosen = []
used_indices = set()

for item in chosen:

    if item["index"] not in used_indices:

        unique_chosen.append(item)
        used_indices.add(item["index"])


chosen = unique_chosen[:10]


# ------------------------------------------------------------
# Build demo CSV
# ------------------------------------------------------------

demo_rows = []

expected_rows = []

for demo_number, item in enumerate(chosen, start=1):

    original_index = item["index"]

    row = df.iloc[original_index]

    demo_rows.append(
        row[feature_names].to_dict()
    )

    expected_rows.append(
        {
            "Demo_Row": demo_number,
            "Original_Dataset_Row": original_index,
            "Prediction": item["prediction"],
            "Confidence_Percent": round(
                item["confidence"] * 100,
                2
            ),
            "Expected_Risk": item["risk"],
            "Actual_Label": str(row[label_column]),
        }
    )


demo_df = pd.DataFrame(demo_rows)

expected_df = pd.DataFrame(expected_rows)


# ------------------------------------------------------------
# Save files
# ------------------------------------------------------------

demo_csv = OUTPUT_DIR / "SecureSense_Demo_10_Rows.csv"

expected_csv = (
    OUTPUT_DIR
    / "SecureSense_Demo_10_Expected_Results.csv"
)

expected_excel = (
    OUTPUT_DIR
    / "SecureSense_Demo_10_Expected_Results.xlsx"
)

demo_df.to_csv(
    demo_csv,
    index=False
)

expected_df.to_csv(
    expected_csv,
    index=False
)

expected_df.to_excel(
    expected_excel,
    index=False
)


# ------------------------------------------------------------
# Print final results
# ------------------------------------------------------------

print()
print("=" * 70)
print("10-ROW DEMO CREATED SUCCESSFULLY")
print("=" * 70)

print()
print(expected_df.to_string(index=False))

print()
print("UPLOAD THIS FILE TO SECURESENSE:")
print(demo_csv)

print()
print("REFERENCE CSV:")
print(expected_csv)

print()
print("REFERENCE EXCEL:")
print(expected_excel)

print()
print("IMPORTANT:")
print(
    "The upload CSV contains ONLY the 69 model features."
)

print(
    "Prediction, confidence and risk are generated by SecureSense."
)

print()
print("=" * 70)