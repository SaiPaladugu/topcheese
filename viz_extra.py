"""
Advanced diagnostics for the dashboard — the filthy, over-engineered, barely-useful,
extremely-stunning tier. Ranked solo (queue 420) only.

Writes small display aggregates into analysis.json["advanced"], and big grids/curves
into advanced_viz.json (consumed only by viz_charts.py, kept out of the web bundle).
"""
import os
import csv
import json
import math
import datetime as dt
from collections import defaultdict, Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
TDIR = os.path.join(RAW, "timelines")
OUT = os.path.join(HERE, "data", "processed")
ME = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"
MAPMAX = 14870
UTC_OFFSET = -6  # inferred earlier


def team_gold(pf, blue):
    rng = range(1, 6) if blue else range(6, 11)
    erng = range(6, 11) if blue else range(1, 6)
    mine = sum(pf[str(i)]["totalGold"] for i in rng)
    opp = sum(pf[str(i)]["totalGold"] for i in erng)
    return mine - opp


def grade(ratio, lower_better=False):
    r = (2 - ratio) if lower_better else ratio
    if r >= 1.12: return "A+"
    if r >= 1.06: return "A"
    if r >= 1.02: return "B"
    if r >= 0.98: return "C"
    if r >= 0.93: return "D"
    return "F"


def main():
    # accumulators
    ekg_w = defaultdict(list)   # minute -> [gold diffs] in wins
    ekg_l = defaultdict(list)   # minute -> [gold diffs] in losses
    g15_buckets = defaultdict(lambda: [0, 0])  # bucket -> [wins, games]
    hour_wd = np.zeros((7, 24, 2))             # [day][hour] = [wins, games]
    posgrid = np.zeros((50, 50))               # his position density (side-normalized)
    kill_pts, death_pts = [], []
    mk = Counter()                             # multikills
    dmg = {"physical": 0, "magic": 0, "true": 0}
    matchup_g = defaultdict(lambda: [0, 0])    # (hisChamp, enemyAdc) -> [wins, games]
    champ_games = Counter(); enemy_games = Counter()

    for fn in os.listdir(MDIR):
        m = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))["info"]
        if m.get("queueId") != 420:
            continue
        me = next((p for p in m["participants"] if p["puuid"] == ME), None)
        if not me:
            continue
        win = bool(me.get("win"))
        tid = me["teamId"]
        blue = (tid == 100)
        pid = me["participantId"]

        # multikills + damage mix
        for k, kk in [("doubleKills", "x2"), ("tripleKills", "x3"),
                      ("quadraKills", "x4"), ("pentaKills", "x5")]:
            mk[kk] += me.get(k, 0)
        dmg["physical"] += me.get("physicalDamageDealtToChampions", 0)
        dmg["magic"] += me.get("magicDamageDealtToChampions", 0)
        dmg["true"] += me.get("trueDamageDealtToChampions", 0)

        # matchup matrix
        champ_games[me["championName"]] += 1
        enemy = next((p for p in m["participants"]
                      if p.get("teamId") != tid and p.get("teamPosition") == "BOTTOM"), None)
        if enemy:
            enemy_games[enemy["championName"]] += 1
            d = matchup_g[(me["championName"], enemy["championName"])]
            d[1] += 1; d[0] += win

        # hour x weekday
        local = dt.datetime.fromtimestamp(m.get("gameCreation", 0) / 1000, dt.timezone.utc) + dt.timedelta(hours=UTC_OFFSET)
        hour_wd[local.weekday()][local.hour][1] += 1
        hour_wd[local.weekday()][local.hour][0] += win

        tp = os.path.join(TDIR, fn)
        if not os.path.exists(tp):
            continue
        frames = json.load(open(tp, encoding="utf-8"))["info"]["frames"]
        for mi, fr in enumerate(frames):
            pf = fr.get("participantFrames", {})
            if str(pid) in pf and mi <= 40:
                diff = team_gold(pf, blue)
                (ekg_w if win else ekg_l)[mi].append(diff)
                pos = pf[str(pid)].get("position")
                if pos:
                    x, y = pos["x"], pos["y"]
                    xn, yn = (x, y) if blue else (MAPMAX - x, MAPMAX - y)
                    gx = min(49, int(xn / MAPMAX * 50))
                    gy = min(49, int(yn / MAPMAX * 50))
                    posgrid[gy][gx] += 1
            if mi == 15 and str(pid) in pf:
                diff = team_gold(pf, blue)
                b = max(-6, min(6, int(round(diff / 1000))))
                bb = (b // 2) * 2
                g15_buckets[bb][1] += 1
                g15_buckets[bb][0] += win
            for ev in fr.get("events", []):
                if ev.get("type") != "CHAMPION_KILL":
                    continue
                pos = ev.get("position")
                if not pos:
                    continue
                x, y = pos["x"], pos["y"]
                xn, yn = (x, y) if blue else (MAPMAX - x, MAPMAX - y)
                if ev.get("victimId") == pid:
                    death_pts.append([round(xn), round(yn)])
                elif ev.get("killerId") == pid or pid in (ev.get("assistingParticipantIds") or []):
                    kill_pts.append([round(xn), round(yn)])

    # ---- gold EKG ----
    minutes = sorted(set(list(ekg_w) + list(ekg_l)))
    ekg = [{"min": mi,
            "win": round(np.mean(ekg_w[mi]), 0) if ekg_w[mi] else None,
            "loss": round(np.mean(ekg_l[mi]), 0) if ekg_l[mi] else None}
           for mi in minutes if mi <= 40]

    # ---- win prob by gold@15 ----
    winprob = []
    for b in sorted(g15_buckets):
        w, g = g15_buckets[b]
        if g >= 5:
            winprob.append({"k": b, "label": f"{b:+d}k", "games": g,
                            "wr": round(100 * w / g, 1)})

    # ---- correlation matrix from ranked_solo.csv ----
    csv_path = os.path.join(OUT, "ranked_solo.csv")
    cols = ["win", "csPerMin", "killParticipation", "teamDmgPct", "deaths", "deadPct",
            "kda", "goldDiff14", "csDiff14", "visionPerMin", "soloKills", "dmgPerMin",
            "laneMinions10", "controlWards"]
    nice = ["WIN", "CS/min", "KP%", "Dmg%", "Deaths", "Dead%", "KDA", "GD@14",
            "CSD@14", "Vis/min", "SoloK", "DPM", "CS@10", "CtrlWd"]
    data = {c: [] for c in cols}
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for c in cols:
                try:
                    data[c].append(float(row[c]))
                except (ValueError, TypeError):
                    data[c].append(np.nan)
    mat = np.array([data[c] for c in cols], float)
    corr = np.ma.corrcoef(np.ma.masked_invalid(mat)).filled(0)

    # ---- matchup matrix (top champs x top enemies) ----
    top_champs = [c for c, _ in champ_games.most_common(6)]
    top_enemies = [c for c, _ in enemy_games.most_common(9)]
    mm_wr, mm_g = [], []
    for ch in top_champs:
        rw, rg = [], []
        for en in top_enemies:
            w, g = matchup_g.get((ch, en), [0, 0])
            rw.append(round(100 * w / g, 0) if g >= 2 else None)
            rg.append(g)
        mm_wr.append(rw); mm_g.append(rg)

    # ---- report card ----
    A = json.load(open(os.path.join(OUT, "analysis.json"), encoding="utf-8"))
    hm = A["benchmark"]["hisMeans"]; bm = A["benchmark"]["means"]
    card = []
    for key, label, lower in [("csPerMin", "Farming", False), ("kp", "Teamfighting", False),
                              ("teamDmgPct", "Carrying", False), ("dmgPerMin", "Damage", False),
                              ("goldPerMin", "Economy", False), ("deaths", "Not Dying", True),
                              ("visionPerMin", "Vision", False), ("controlWards", "Warding", False),
                              ("soloKills", "Dueling", False)]:
        ratio = (hm[key] / bm[key]) if bm[key] else 1
        card.append({"category": label, "him": hm[key], "dia": bm[key],
                     "grade": grade(ratio, lower)})

    advanced_display = {
        "winProb15": winprob,
        "multikills": dict(mk),
        "damageMix": dmg,
        "reportCard": card,
        "matchup": {"champs": top_champs, "enemies": top_enemies, "wr": mm_wr, "games": mm_g},
        "hourWeekday": [[{"wins": int(hour_wd[d][h][0]), "games": int(hour_wd[d][h][1])}
                         for h in range(24)] for d in range(7)],
    }
    A["advanced"] = advanced_display
    json.dump(A, open(os.path.join(OUT, "analysis.json"), "w", encoding="utf-8"), indent=2)

    viz = {
        "ekg": ekg,
        "corr": {"labels": nice, "matrix": [[round(x, 2) for x in row] for row in corr]},
        "posgrid": posgrid.tolist(),
        "killPts": kill_pts,
        "deathPts": death_pts,
        "hourWeekday": advanced_display["hourWeekday"],
        "matchup": advanced_display["matchup"],
        "winProb15": winprob,
        "damageMix": dmg,
        "multikills": dict(mk),
    }
    json.dump(viz, open(os.path.join(OUT, "advanced_viz.json"), "w"), separators=(",", ":"))

    print("EKG minutes:", len(ekg), "| corr:", corr.shape, "| kills:", len(kill_pts),
          "deaths:", len(death_pts))
    print("winProb15:", [(w["label"], w["wr"]) for w in winprob])
    print("multikills:", dict(mk), "| dmgMix:", dmg)
    print("report card:", [(c["category"], c["grade"]) for c in card])


if __name__ == "__main__":
    main()
