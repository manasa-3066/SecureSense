import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# ============================================================
# SECURESENSE - FIGURE 8
# GENERALIZATION PERFORMANCE COMPARISON
# ============================================================

OUTPUT_DIR = Path("results/final_curves")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

metrics = [
    "Accuracy",
    "Precision",
    "Recall",
    "F1-score",
    "ROC-AUC"
]

stratified = [
    99.25,
    95.95,
    99.20,
    97.54,
    99.97
]

unseen_source = [
    90.58,
    95.19,
    52.96,
    68.05,
    90.15
]

x = np.arange(len(metrics))
width = 0.34

fig, ax = plt.subplots(figsize=(10, 6), dpi=600)

bars1 = ax.bar(
    x - width / 2,
    stratified,
    width,
    label="Stratified Evaluation"
)

bars2 = ax.bar(
    x + width / 2,
    unseen_source,
    width,
    label="Unseen-Source Evaluation"
)

ax.set_ylabel("Performance (%)", fontsize=13)
ax.set_xticks(x)
ax.set_xticklabels(metrics, fontsize=11)

ax.set_ylim(0, 105)

ax.grid(
    axis="y",
    linestyle=":",
    linewidth=0.8,
    alpha=0.7
)

ax.set_axisbelow(True)

# Add exact values above bars
for bars in [bars1, bars2]:
    for bar in bars:
        value = bar.get_height()

        ax.annotate(
            f"{value:.2f}",
            xy=(
                bar.get_x() + bar.get_width() / 2,
                value
            ),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9
        )

ax.legend(
    loc="lower left",
    fontsize=10,
    frameon=True
)

# No large internal title:
# IEEE-style papers normally use the caption below the figure.

fig.tight_layout()

output_file = OUTPUT_DIR / "Figure_8_Generalization_Comparison.png"

fig.savefig(
    output_file,
    dpi=600,
    bbox_inches="tight"
)

plt.close(fig)

print("=" * 70)
print("SECURESENSE - FIGURE 8 GENERATED")
print("=" * 70)
print(f"Output: {output_file}")
print()
print("Verified values:")
for metric, s, u in zip(metrics, stratified, unseen_source):
    print(f"{metric:12s}: {s:.2f}% -> {u:.2f}%")
print("=" * 70)
