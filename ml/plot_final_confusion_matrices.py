import os
import matplotlib.pyplot as plt
import numpy as np

RESULTS_DIR = "results/final_primary_dnn"


def save_confusion_matrix(cm, filename):
    fig, ax = plt.subplots(figsize=(4.8, 4.0))

    # White cells with black borders — IEEE-style
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)

    # Draw 2x2 grid
    for x in range(3):
        ax.plot([x, x], [0, 2], color="black", linewidth=1.0)

    for y in range(3):
        ax.plot([0, 2], [y, y], color="black", linewidth=1.0)

    # Values
    for i in range(2):
        for j in range(2):
            ax.text(
                j + 0.5,
                1.5 - i,
                f"{cm[i, j]:,}",
                ha="center",
                va="center",
                fontsize=12,
                fontweight="bold"
            )

    ax.set_xticks([0.5, 1.5])
    ax.set_yticks([1.5, 0.5])

    ax.set_xticklabels(["BENIGN", "ATTACK"], fontsize=10)
    ax.set_yticklabels(["BENIGN", "ATTACK"], fontsize=10)

    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("Actual Label", fontsize=11)

    # No internal title — IEEE caption will provide it
    ax.set_aspect("equal")

    # Remove unnecessary outer spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.tight_layout()

    plt.savefig(
        os.path.join(RESULTS_DIR, filename),
        dpi=600,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close()


# ============================================================
# FIG. 4 — PRIMARY STRATIFIED EVALUATION
# ============================================================

cm_primary = np.array([
    [188096, 1409],
    [270, 33352]
])

save_confusion_matrix(
    cm_primary,
    "Fig_4_Primary_Confusion_Matrix.png"
)


# ============================================================
# FIG. 5 — UNSEEN-SOURCE EVALUATION
# ============================================================

cm_unseen = np.array([
    [543888, 3425],
    [60221, 67790]
])

save_confusion_matrix(
    cm_unseen,
    "Fig_5_Unseen_Source_Confusion_Matrix.png"
)

print("Fig. 4 and Fig. 5 saved successfully.")