"""
Render the advanced diagnostic visuals into web/public/charts/.
Reads advanced_viz.json + analysis.json. Run after viz_extra.py.
"""
import os
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "web", "public", "charts")
os.makedirs(OUT, exist_ok=True)
V = json.load(open(os.path.join(HERE, "data", "processed", "advanced_viz.json")))
A = json.load(open(os.path.join(HERE, "data", "processed", "analysis.json"), encoding="utf-8"))

BG = "#0f1419"; FG = "#e6edf3"; GRID = "#30363d"
WIN = "#3fb950"; LOSS = "#f85149"; ACC = "#58a6ff"; ACC2 = "#d29922"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
    "axes.edgecolor": GRID, "grid.color": GRID, "font.size": 11,
    "axes.titlecolor": FG, "figure.dpi": 120,
})
HEAT = LinearSegmentedColormap.from_list("heat", ["#0f1419", "#3b1f47", "#b83280", "#f85149", "#ffd166"])
WRMAP = LinearSegmentedColormap.from_list("wr", [LOSS, "#caa23a", WIN])


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight")
    plt.close(fig)
    print(" ", name)


def radar():
    keys = [("csPerMin", "CS/min"), ("kp", "Kill\npart."), ("teamDmgPct", "Team\ndmg%"),
            ("dmgPerMin", "DPM"), ("goldPerMin", "Gold/min"), ("soloKills", "Solo\nkills"),
            ("visionPerMin", "Vision"), ("controlWards", "Ctrl\nwards")]
    hm, bm = A["benchmark"]["hisMeans"], A["benchmark"]["means"]
    him = [hm[k] / bm[k] if bm[k] else 1 for k, _ in keys]
    dia = [1.0] * len(keys)
    labels = [lbl for _, lbl in keys]
    ang = np.linspace(0, 2 * np.pi, len(keys), endpoint=False).tolist()
    him += him[:1]; dia += dia[:1]; ang += ang[:1]
    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw=dict(polar=True))
    ax.set_facecolor(BG)
    ax.plot(ang, dia, color=ACC2, lw=1.5, ls="--", label="Diamond ADC (par)")
    ax.fill(ang, dia, color=ACC2, alpha=0.08)
    ax.plot(ang, him, color=LOSS, lw=2.2, label="The chud")
    ax.fill(ang, him, color=LOSS, alpha=0.25)
    ax.set_xticks(ang[:-1]); ax.set_xticklabels(labels, fontsize=10)
    ax.set_yticks([0.5, 0.75, 1.0]); ax.set_yticklabels(["", "", "rank avg"], fontsize=8)
    ax.set_ylim(0, 1.2)
    ax.set_title("The chud vs his own rank, every axis (Diamond avg = 1.0)\nhe is inside the line on almost everything", pad=24)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.12), facecolor=BG, edgecolor=GRID, labelcolor=FG)
    save(fig, "radar.png")


def gold_ekg():
    ekg = V["ekg"]
    mins = [e["min"] for e in ekg]
    w = [e["win"] for e in ekg]
    l = [e["loss"] for e in ekg]
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(mins, w, color=WIN, lw=2.4, label="in his WINS")
    ax.plot(mins, l, color=LOSS, lw=2.4, label="in his LOSSES")
    ax.fill_between(mins, 0, w, color=WIN, alpha=0.12)
    ax.fill_between(mins, 0, l, color=LOSS, alpha=0.12)
    ax.axhline(0, color=FG, lw=0.8)
    ax.set_title("Team gold-diff EKG — averaged across every game, minute by minute")
    ax.set_xlabel("minute"); ax.set_ylabel("team gold lead (his side)")
    ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG); ax.grid(alpha=0.25)
    save(fig, "gold_ekg.png")


def winprob():
    wp = V["winProb15"]
    x = [w["k"] for w in wp]; y = [w["wr"] for w in wp]; g = [w["games"] for w in wp]
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(x, y, color=ACC, lw=2.6, marker="o", markersize=8, markerfacecolor=ACC, markeredgecolor=FG)
    ax.fill_between(x, 50, y, where=[v >= 50 for v in y], color=WIN, alpha=0.15, interpolate=True)
    ax.fill_between(x, 50, y, where=[v < 50 for v in y], color=LOSS, alpha=0.15, interpolate=True)
    ax.axhline(50, color=GRID, ls="--")
    for xi, yi, gi in zip(x, y, g):
        ax.annotate(f"{yi}%", (xi, yi), textcoords="offset points", xytext=(0, 10), ha="center", fontsize=9, color=FG)
    ax.set_title("Win probability vs his team's gold lead at 15:00\nthe game is basically decided by minute 15")
    ax.set_xlabel("team gold lead at 15 min (k)"); ax.set_ylabel("win rate %")
    ax.set_ylim(0, 100); ax.grid(alpha=0.25)
    save(fig, "winprob.png")


def corr_heatmap():
    labels = V["corr"]["labels"]
    M = np.array(V["corr"]["matrix"])
    n = len(labels)
    fig, ax = plt.subplots(figsize=(9.5, 8.5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(n)); ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(n)); ax.set_yticklabels(labels, fontsize=9)
    for i in range(n):
        for j in range(n):
            v = M[i][j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if abs(v) > 0.5 else "#9aa4b2", fontsize=6.5)
    ax.set_title("Diagnostic correlation matrix of his every metric\n(top row = what actually correlates with WINNING)", pad=12)
    fig.colorbar(im, ax=ax, shrink=0.7, label="Pearson r")
    save(fig, "corr_heatmap.png")


def matchup_heatmap():
    mm = V["matchup"]
    champs, enemies = mm["champs"], mm["enemies"]
    W = np.array([[np.nan if v is None else v for v in row] for row in mm["wr"]], float)
    G = mm["games"]
    fig, ax = plt.subplots(figsize=(10, 5.6))
    im = ax.imshow(W, cmap=WRMAP, vmin=20, vmax=80, aspect="auto")
    ax.set_xticks(range(len(enemies))); ax.set_xticklabels(enemies, rotation=35, ha="right")
    ax.set_yticks(range(len(champs))); ax.set_yticklabels(champs)
    for i in range(len(champs)):
        for j in range(len(enemies)):
            if not np.isnan(W[i][j]):
                ax.text(j, i, f"{int(W[i][j])}%\n{G[i][j]}g", ha="center", va="center",
                        fontsize=7, color="black" if 35 < W[i][j] < 70 else "white")
    ax.set_title("Matchup matrix — his champ (rows) vs enemy ADC (cols), win %", pad=10)
    fig.colorbar(im, ax=ax, shrink=0.8, label="win %")
    save(fig, "matchup_heatmap.png")


def hourweekday():
    HW = V["hourWeekday"]
    wr = np.full((7, 24), np.nan)
    for d in range(7):
        for h in range(24):
            c = HW[d][h]
            if c["games"] >= 2:
                wr[d][h] = 100 * c["wins"] / c["games"]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    fig, ax = plt.subplots(figsize=(11, 3.8))
    im = ax.imshow(wr, cmap=WRMAP, vmin=30, vmax=70, aspect="auto")
    ax.set_yticks(range(7)); ax.set_yticklabels(days)
    ax.set_xticks(range(0, 24, 2)); ax.set_xticklabels([f"{h}:00" for h in range(0, 24, 2)], fontsize=8)
    ax.set_title("When the chud wins — win rate by hour × weekday (local time, ≥2 games)\nbright = winning, red = tilting, blank = asleep or has a life")
    ax.set_xlabel("hour of day")
    fig.colorbar(im, ax=ax, shrink=0.85, label="win %")
    save(fig, "hourweekday.png")


def loiter_map():
    grid = np.array(V["posgrid"])
    grid = np.log1p(grid)
    fig, ax = plt.subplots(figsize=(7, 7))
    im = ax.imshow(grid, cmap=HEAT, origin="lower", extent=(0, 1, 0, 1))
    ax.plot([0, 1], [1, 0], color=ACC, ls="--", lw=1, alpha=0.5)
    ax.text(0.04, 0.04, "HIS BASE", color=WIN, fontweight="bold", fontsize=10)
    ax.text(0.74, 0.92, "ENEMY BASE", color=LOSS, fontweight="bold", fontsize=10)
    ax.text(0.72, 0.05, "bot lane", color=FG, fontsize=9, alpha=0.7)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Where this chud actually spends the game\n(position density, all games side-normalized)")
    save(fig, "loiter_map.png")


def killdeath_map():
    def grid(pts):
        g = np.zeros((40, 40))
        for x, y in pts:
            gx = min(39, int(x / 14870 * 40)); gy = min(39, int(y / 14870 * 40))
            g[gy][gx] += 1
        return g
    k = grid(V["killPts"]); d = grid(V["deathPts"])
    net = k / (k.max() or 1) - d / (d.max() or 1)
    fig, ax = plt.subplots(figsize=(7, 7))
    im = ax.imshow(net, cmap="RdYlGn", origin="lower", extent=(0, 1, 0, 1),
                   norm=TwoSlopeNorm(vcenter=0, vmin=-1, vmax=1))
    ax.plot([0, 1], [1, 0], color="#222", ls="--", lw=1)
    ax.text(0.04, 0.04, "HIS BASE", color="#0b6", fontweight="bold", fontsize=10)
    ax.text(0.72, 0.92, "ENEMY BASE", color="#900", fontweight="bold", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Kill/death territory map — green = he kills here, red = he dies here\n(net density, side-normalized)")
    fig.colorbar(im, ax=ax, shrink=0.8, label="← dies   ·   kills →")
    save(fig, "killdeath_map.png")


def damage_donut():
    dm = V["damageMix"]
    vals = [dm["physical"], dm["magic"], dm["true"]]
    labels = ["Physical", "Magic", "True"]
    cols = [ACC, "#b083f0", FG]
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    w, _, _ = ax.pie(vals, labels=labels, colors=cols, autopct="%1.0f%%",
                     pctdistance=0.78, wedgeprops=dict(width=0.42, edgecolor=BG),
                     textprops=dict(color=FG))
    ax.set_title("His lifetime damage mix\n(one-dimensional, like his gameplay)")
    save(fig, "damage_donut.png")


def main():
    print("Rendering advanced visuals -> web/public/charts/")
    radar(); gold_ekg(); winprob(); corr_heatmap(); matchup_heatmap()
    hourweekday(); loiter_map(); killdeath_map(); damage_donut()
    print("Done.")


if __name__ == "__main__":
    main()
