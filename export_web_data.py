"""
Export compact data for the interactive/3D client visuals into web/data/:
  games.json   — one row per ranked-solo game (for the 3D scatter)
  surface.json — win% surface over (gold@14 × kill-participation) buckets
  terrain.json — 32×32 death-density heightfield (for the r3f 3D terrain)
"""
import os
import csv
import json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(HERE, "data", "processed")
WEB = os.path.join(HERE, "web", "data")
os.makedirs(WEB, exist_ok=True)


def main():
    # ---- per-game points ----
    games = []
    with open(os.path.join(PROC, "ranked_solo.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                g14 = float(r["goldDiff14"]); kp = float(r["killParticipation"])
                d = int(r["deaths"]); cs = float(r["csPerMin"])
            except (ValueError, TypeError, KeyError):
                continue
            games.append({"g14": round(g14), "kp": round(kp, 1), "d": d,
                          "cs": round(cs, 2), "win": int(r["win"]),
                          "champ": r["champion"]})
    json.dump(games, open(os.path.join(WEB, "games.json"), "w"), separators=(",", ":"))

    # ---- win% surface over gold@14 × KP ----
    gx = list(range(-3000, 3001, 1000))          # gold@14 bucket left edges
    ky = list(range(20, 71, 10))                  # KP bucket left edges
    Z = [[None] * len(gx) for _ in ky]
    cells = [[[0, 0] for _ in gx] for _ in ky]
    for p in games:
        gi = min(range(len(gx)), key=lambda i: abs(p["g14"] - (gx[i] + 500)))
        # only count if within bucket span
        if not (gx[0] - 500 <= p["g14"] <= gx[-1] + 1500):
            continue
        gi = max(0, min(len(gx) - 1, (p["g14"] - (gx[0])) // 1000))
        ki = max(0, min(len(ky) - 1, int((p["kp"] - ky[0]) // 10)))
        gi = int(gi)
        cells[ki][gi][1] += 1
        cells[ki][gi][0] += p["win"]
    for i in range(len(ky)):
        for j in range(len(gx)):
            w, g = cells[i][j]
            if g >= 3:
                Z[i][j] = round(100 * w / g, 1)
    json.dump({"x": gx, "y": ky, "z": Z}, open(os.path.join(WEB, "surface.json"), "w"))

    # ---- death-density terrain (32×32) ----
    viz = json.load(open(os.path.join(PROC, "advanced_viz.json")))
    N = 32
    grid = np.zeros((N, N))
    for x, y in viz["deathPts"]:
        gx2 = min(N - 1, int(x / 14870 * N)); gy2 = min(N - 1, int(y / 14870 * N))
        grid[gy2][gx2] += 1
    # light smoothing
    sm = grid.copy()
    for _ in range(2):
        sm = (sm
              + np.roll(sm, 1, 0) + np.roll(sm, -1, 0)
              + np.roll(sm, 1, 1) + np.roll(sm, -1, 1)) / 5.0
    sm = sm / (sm.max() or 1)
    json.dump({"n": N, "h": [[round(float(v), 4) for v in row] for row in sm]},
              open(os.path.join(WEB, "terrain.json"), "w"))

    print(f"games: {len(games)} | surface {len(ky)}x{len(gx)} | terrain {N}x{N}")


if __name__ == "__main__":
    main()
