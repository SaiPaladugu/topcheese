"""
Generate charts from data/processed/analysis.json into web/public/charts/.
Run after analyze.py. Pure matplotlib, dark theme to match the dashboard.
"""
import os
import json
import datetime as dt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
A = json.load(open(os.path.join(HERE, "data", "processed", "analysis.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "web", "public", "charts")
os.makedirs(OUT, exist_ok=True)

# theme
BG = "#0f1419"; FG = "#e6edf3"; GRID = "#30363d"
WIN = "#3fb950"; LOSS = "#f85149"; ACC = "#58a6ff"; ACC2 = "#d29922"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": FG, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
    "axes.edgecolor": GRID, "grid.color": GRID, "font.size": 11,
    "axes.titlecolor": FG, "figure.dpi": 120,
})
LINE50 = dict(color=GRID, ls="--", lw=1)


def save(fig, name):
    fig.tight_layout()
    p = os.path.join(OUT, name)
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}")


def bar_wr(items, title, fname, label_key="bucket", order_as_given=True, ref=51.5):
    items = [b for b in items if b["games"] > 0]
    labels = [str(b[label_key]) for b in items]
    wr = [b["wr"] for b in items]
    games = [b["games"] for b in items]
    colors = [WIN if v >= ref else LOSS for v in wr]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, wr, color=colors, edgecolor=GRID)
    ax.axhline(ref, **LINE50)
    ax.text(len(labels) - 0.5, ref + 0.6, f"his avg {ref}%", color=GRID, ha="right", fontsize=9)
    for b, g, v in zip(bars, games, wr):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v}%\n({g}g)",
                ha="center", va="bottom", fontsize=8, color=FG)
    ax.set_title(title); ax.set_ylabel("Win rate %")
    ax.set_ylim(0, max(wr) + 12)
    ax.grid(axis="y", alpha=0.3)
    save(fig, fname)


def chart_champion_wr():
    champs = [c for c in A["champions"] if c["games"] >= 10]
    champs.sort(key=lambda c: c["wr"])
    labels = [f"{c['champion']} ({c['games']})" for c in champs]
    wr = [c["wr"] for c in champs]
    colors = [WIN if v >= 51.5 else (LOSS if v < 48 else ACC2) for v in wr]
    fig, ax = plt.subplots(figsize=(8, max(4, 0.45 * len(champs) + 1)))
    ax.barh(labels, wr, color=colors, edgecolor=GRID)
    ax.axvline(51.5, **LINE50)
    for i, v in enumerate(wr):
        ax.text(v + 0.4, i, f"{v}%", va="center", fontsize=8, color=FG)
    ax.set_title("Win rate by champion (≥10 games)")
    ax.set_xlabel("Win rate %"); ax.set_xlim(0, max(wr) + 8)
    ax.grid(axis="x", alpha=0.3)
    save(fig, "champion_wr.png")


def chart_winloss_effect():
    rows = [r for r in A["winLoss"] if r["cohensD"] is not None and r["key"] not in ("durationMin",)]
    rows = rows[:12][::-1]
    labels = [r["label"] for r in rows]
    d = [r["cohensD"] for r in rows]
    colors = [WIN if x >= 0 else LOSS for x in d]
    fig, ax = plt.subplots(figsize=(8.5, 6))
    ax.barh(labels, d, color=colors, edgecolor=GRID)
    ax.axvline(0, color=FG, lw=0.8)
    for i, x in enumerate(d):
        ax.text(x + (0.02 if x >= 0 else -0.02), i, f"{x:+.2f}",
                va="center", ha="left" if x >= 0 else "right", fontsize=8, color=FG)
    ax.set_title("What separates his WINS from LOSSES\n(Cohen's d effect size; bigger = more decisive)")
    ax.set_xlabel("effect size (win mean − loss mean, standardized)")
    ax.grid(axis="x", alpha=0.3)
    save(fig, "winloss_effect.png")


def chart_gold14_dist():
    # rebuild from raw via per-game is not stored; approximate using means from winLoss
    # Instead show win/loss means for the @14 lane metrics as grouped bars.
    keys = [("goldDiff14", "Gold diff @14"), ("csDiff14", "CS diff @14"),
            ("xpDiff14", "XP diff @14")]
    wl = {r["key"]: r for r in A["winLoss"]}
    labels = [lbl for k, lbl in keys if k in wl]
    wins = [wl[k]["winMean"] for k, _ in keys if k in wl]
    losses = [wl[k]["lossMean"] for k, _ in keys if k in wl]
    x = np.arange(len(labels)); wd = 0.38
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - wd / 2, wins, wd, label="in WINS", color=WIN, edgecolor=GRID)
    ax.bar(x + wd / 2, losses, wd, label="in LOSSES", color=LOSS, edgecolor=GRID)
    ax.axhline(0, color=FG, lw=0.8)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_title("Lane lead at 14 min: wins vs losses")
    ax.set_ylabel("difference vs lane opponent"); ax.legend()
    ax.grid(axis="y", alpha=0.3)
    save(fig, "lane14_winloss.png")


def chart_form():
    form = A["form"]
    xs = [dt.datetime.fromtimestamp(f["ts"], dt.timezone.utc) for f in form]
    ys = [f["rollingWR"] for f in form]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(xs, ys, color=ACC, lw=1.6)
    ax.fill_between(xs, 50, ys, where=[y >= 50 for y in ys], color=WIN, alpha=0.18, interpolate=True)
    ax.fill_between(xs, 50, ys, where=[y < 50 for y in ys], color=LOSS, alpha=0.18, interpolate=True)
    ax.axhline(50, **LINE50)
    ax.set_title("Recent form: rolling 50-game win rate")
    ax.set_ylabel("win rate %"); ax.grid(alpha=0.3)
    save(fig, "form.png")


def chart_benchmark():
    b = A.get("benchmark")
    if not b:
        return
    keys = [("csPerMin", "CS/min"), ("kp", "Kill part. %"), ("teamDmgPct", "Team dmg %"),
            ("dmgPerMin", "Dmg/min"), ("goldPerMin", "Gold/min"), ("visionPerMin", "Vision/min"),
            ("controlWards", "Ctrl wards"), ("soloKills", "Solo kills"), ("deaths", "Deaths")]
    himeans = b["hisMeans"]
    labels = [lbl for k, lbl in keys]
    him = [himeans[k] for k, _ in keys]
    dia = [b["means"][k] for k, _ in keys]
    # normalize each metric as ratio him/diamond for a fair single-axis view
    ratio = [(h / d * 100 if d else 100) for h, d in zip(him, dia)]
    colors = [WIN if (r >= 100 and lbl != "Deaths") or (r < 100 and lbl == "Deaths") else LOSS
              for r, lbl in zip(ratio, labels)]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.bar(labels, ratio, color=colors, edgecolor=GRID)
    ax.axhline(100, **LINE50)
    ax.text(len(labels) - 0.5, 101.5, "Diamond ADC avg = 100", color=GRID, ha="right", fontsize=9)
    for bar, h, d in zip(bars, him, dia):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
                f"{h:.1f}\nvs {d:.1f}", ha="center", va="bottom", fontsize=7, color=FG)
    ax.set_title("Him vs Diamond-ADC baseline (100 = at rank average)\nfor Deaths, lower is better")
    ax.set_ylabel("% of Diamond average")
    ax.set_ylim(0, max(ratio) + 14); ax.grid(axis="y", alpha=0.3)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    save(fig, "benchmark.png")


def chart_support():
    soc = A.get("social")
    if not soc or not soc.get("support"):
        return
    sups = sorted(soc["support"], key=lambda s: s["wr"])
    labels = [f"{s['champion']} ({s['games']})" for s in sups]
    val = [s["wr"] for s in sups]
    colors = [WIN if v >= 51.5 else (LOSS if v < 48 else ACC2) for v in val]
    fig, ax = plt.subplots(figsize=(8.5, max(5, 0.36 * len(sups) + 1)))
    ax.barh(labels, val, color=colors, edgecolor=GRID)
    ax.axvline(51.5, **LINE50)
    for i, v in enumerate(val):
        ax.text(v + 0.5, i, f"{v}%", va="center", fontsize=8, color=FG)
    ax.set_title("His win rate by support champion in his lane (≥12 games)\nNami (49g) sinks him · Thresh (47g) lifts him · 33%→69% swing")
    ax.set_xlabel("Win rate %"); ax.set_xlim(0, max(val) + 9)
    ax.grid(axis="x", alpha=0.3)
    save(fig, "support_wr.png")


def chart_gamelength():
    soc = A.get("social")
    if not soc or not soc.get("gameLength"):
        return
    g = soc["gameLength"]
    labels = [x["bucket"] for x in g]
    val = [x["wr"] for x in g]
    colors = [WIN if v >= 51.5 else LOSS for v in val]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    bars = ax.bar(labels, val, color=colors, edgecolor=GRID)
    ax.axhline(51.5, **LINE50)
    for b, x in zip(bars, g):
        ax.text(b.get_x() + b.get_width() / 2, x["wr"] + 0.4, f"{x['wr']}%\n({x['games']}g)",
                ha="center", va="bottom", fontsize=8, color=FG)
    ax.set_title("Win rate by game length — a scaling chud who wins the long ones")
    ax.set_ylabel("Win rate %"); ax.set_ylim(0, max(val) + 12)
    ax.grid(axis="y", alpha=0.3)
    save(fig, "gamelength_wr.png")


def main():
    print("Generating charts -> web/public/charts/")
    chart_support()
    chart_gamelength()
    chart_champion_wr()
    chart_winloss_effect()
    chart_gold14_dist()
    chart_form()
    chart_benchmark()
    bar_wr(A["time"]["byStreak"], "Win rate by streak state (tilt check)", "streak_wr.png")
    bar_wr(A["time"]["byGamesPerDay"], "Win rate by games played that day", "gamesperday_wr.png")
    bar_wr(A["time"]["bySessionGame"], "Win rate by game number within a session", "session_wr.png")
    bar_wr(A["time"]["byHour"], f"Win rate by hour of day (local, UTC{A['time']['inferredUtcOffset']})", "hour_wr.png")
    bar_wr(A["time"]["byWeekday"], "Win rate by day of week", "weekday_wr.png")
    print("Done.")


if __name__ == "__main__":
    main()
