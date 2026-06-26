"""
Three more analyses for Topcheese044 ranked-solo (queue 420):
  (2) Deaths     — timing histogram + map positions (side-normalized to blue) +
                   overextension rate (share of deaths in the enemy half).
  (4) Mastery    — his Champion-Mastery points vs his actual ranked win rate
                   ("comfort picks" that are secretly griefing him).
  (7) Carry      — is he ever the top-damage player on his own team? Damage rank
                   among his 5, % of games he's the team carry, split win/loss.

Merges aggregates into analysis.json; raw death points -> death_points.json.
"""
import os
import json
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
TDIR = os.path.join(RAW, "timelines")
STATIC = os.path.join(HERE, "data", "static")
OUT = os.path.join(HERE, "data", "processed")
ME = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"
MAPMAX = 14870  # Summoner's Rift coordinate extent


def main():
    id2name = json.load(open(os.path.join(STATIC, "champion_id_to_name.json"), encoding="utf-8"))
    id2name = {int(k): v for k, v in id2name.items()}

    death_points = []                 # [minute, xn, yn]  (blue-side normalized)
    death_minute = Counter()          # minute bucket -> count
    enemy_half = own_half = 0
    champ_wr = defaultdict(lambda: [0, 0])  # name -> [wins, games] (his)
    dmg_rank_counts = Counter()       # his damage rank 1..5 -> count
    top_dmg_wins = top_dmg_losses = 0
    games_w = games_l = 0
    gold_rank_counts = Counter()

    for fn in os.listdir(MDIR):
        m = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))["info"]
        if m.get("queueId") != 420:
            continue
        me = next((p for p in m["participants"] if p["puuid"] == ME), None)
        if not me:
            continue
        win = bool(me.get("win"))
        tid = me["teamId"]
        champ_wr[me["championName"]][1] += 1
        champ_wr[me["championName"]][0] += win

        # ---- (7) carry rank among his own team ----
        team = [p for p in m["participants"] if p["teamId"] == tid]
        dmg_sorted = sorted(team, key=lambda p: p.get("totalDamageDealtToChampions", 0), reverse=True)
        gold_sorted = sorted(team, key=lambda p: p.get("goldEarned", 0), reverse=True)
        drank = next(i for i, p in enumerate(dmg_sorted, 1) if p["puuid"] == ME)
        grank = next(i for i, p in enumerate(gold_sorted, 1) if p["puuid"] == ME)
        dmg_rank_counts[drank] += 1
        gold_rank_counts[grank] += 1
        if win:
            games_w += 1
            top_dmg_wins += (drank == 1)
        else:
            games_l += 1
            top_dmg_losses += (drank == 1)

        # ---- (2) death timing + positions ----
        pid = me["participantId"]
        blue = (tid == 100)
        tp = os.path.join(TDIR, fn)
        if os.path.exists(tp):
            for fr in json.load(open(tp, encoding="utf-8"))["info"]["frames"]:
                for ev in fr.get("events", []):
                    if ev.get("type") == "CHAMPION_KILL" and ev.get("victimId") == pid:
                        t = ev.get("timestamp", 0) / 60000.0
                        pos = ev.get("position") or {}
                        x, y = pos.get("x", 0), pos.get("y", 0)
                        xn, yn = (x, y) if blue else (MAPMAX - x, MAPMAX - y)
                        death_points.append([round(t, 1), xn, yn])
                        b = min(int(t // 5) * 5, 35)  # 0,5,10,...35+
                        death_minute[b] += 1
                        if xn + yn > MAPMAX:
                            enemy_half += 1
                        else:
                            own_half += 1

    # ---- (4) mastery vs reality ----
    mastery = json.load(open(os.path.join(RAW, "champion_mastery.json"), encoding="utf-8"))
    mrows = []
    for c in mastery:
        name = id2name.get(c["championId"])
        if not name:
            continue
        wr = champ_wr.get(name)
        if wr and wr[1] >= 8:  # only champs he's actually laddered on
            mrows.append({
                "champion": name,
                "masteryPoints": c.get("championPoints", 0),
                "masteryLevel": c.get("championLevel", 0),
                "games": wr[1],
                "wr": round(100 * wr[0] / wr[1], 1),
            })
    mrows.sort(key=lambda r: -r["masteryPoints"])

    total_d = enemy_half + own_half
    deaths2 = {
        "timing": [{"bucket": f"{b}-{b+5}" if b < 35 else "35+", "minute": b,
                    "count": death_minute[b]} for b in sorted(death_minute)],
        "totalDeaths": total_d,
        "enemyHalfPct": round(100 * enemy_half / total_d, 1) if total_d else None,
        "ownHalfPct": round(100 * own_half / total_d, 1) if total_d else None,
    }
    carry = {
        "dmgRank": [{"rank": r, "games": dmg_rank_counts[r],
                     "pct": round(100 * dmg_rank_counts[r] / sum(dmg_rank_counts.values()), 1)}
                    for r in range(1, 6)],
        "goldRank": [{"rank": r, "games": gold_rank_counts[r],
                      "pct": round(100 * gold_rank_counts[r] / sum(gold_rank_counts.values()), 1)}
                     for r in range(1, 6)],
        "topDmgPctWins": round(100 * top_dmg_wins / games_w, 1) if games_w else None,
        "topDmgPctLosses": round(100 * top_dmg_losses / games_l, 1) if games_l else None,
        "topDmgPctOverall": round(100 * (top_dmg_wins + top_dmg_losses) / (games_w + games_l), 1),
        "avgDmgRank": round(sum(r * dmg_rank_counts[r] for r in range(1, 6)) / sum(dmg_rank_counts.values()), 2),
    }
    mastery_block = {"rows": mrows}

    apath = os.path.join(OUT, "analysis.json")
    A = json.load(open(apath, encoding="utf-8"))
    A["deaths2"] = deaths2
    A["mastery"] = mastery_block
    A["carry"] = carry
    json.dump(A, open(apath, "w", encoding="utf-8"), indent=2)
    json.dump(death_points, open(os.path.join(OUT, "death_points.json"), "w"), separators=(",", ":"))

    print("deaths:", total_d, "| enemy-half %:", deaths2["enemyHalfPct"])
    print("carry: top-dmg overall %", carry["topDmgPctOverall"],
          "| wins", carry["topDmgPctWins"], "losses", carry["topDmgPctLosses"],
          "| avg dmg rank", carry["avgDmgRank"])
    print("mastery top 8 (points -> WR):")
    for r in mrows[:8]:
        print(f"  {r['champion']:<14} {r['masteryPoints']:>8} pts  {r['games']:>3}g  {r['wr']}%")


if __name__ == "__main__":
    main()
