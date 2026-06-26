"""Chart of the model's standardized coefficients -> web/public/charts/ml_coefs.png"""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, "data", "processed", "analysis.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "web", "public", "charts")
BG, FG, GRID, WIN, LOSS = "#0f1419", "#e6edf3", "#30363d", "#3fb950", "#f85149"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                     "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
                     "axes.edgecolor": GRID, "axes.titlecolor": FG, "figure.dpi": 120})

coefs = A["ml"]["coefs"][::-1]
labels = [c["label"] for c in coefs]
vals = [c["coef"] for c in coefs]
colors = [WIN if v >= 0 else LOSS for v in vals]
fig, ax = plt.subplots(figsize=(8.5, 6))
ax.barh(labels, vals, color=colors, edgecolor=GRID)
ax.axvline(0, color=FG, lw=0.8)
for i, v in enumerate(vals):
    ax.text(v + (0.03 if v >= 0 else -0.03), i, f"{v:+.2f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=8, color=FG)
ax.set_title(f"What the algorithm learned predicts his wins\n(logistic-regression weights · {A['ml']['cvAccuracy']}% accurate, AUC {A['ml']['cvAuc']})")
ax.set_xlabel("← makes him LOSE      standardized weight      makes him WIN →")
ax.grid(axis="x", alpha=0.25)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "ml_coefs.png"), bbox_inches="tight")
print("  ml_coefs.png")
