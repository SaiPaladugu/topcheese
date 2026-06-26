"""
Social / contextual analysis for Topcheese044 ranked-solo ADC games:
  - support synergy: his WR by the support champion in his lane
  - squad: most-frequent teammates (premades) and their WR impact
  - game-length WR (early vs scaling)
  - throw / comeback rate from team gold @15 (timelines)
Merges a "social" block into data/processed/analysis.json. Local-only.
"""
import os
import json
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
TDIR = os.path.join(RAW, "timelines")
OUT = os.path.join(HERE, "data", "processed")
ME = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"


def wr(w, g):
    return round(100 * w / g, 1) if g else None


def main():
    sup = defaultdict(lambda: [0, 0])        # support champ -> [wins, games]
    mate = defaultdict(lambda: [0, 0, ""])   # teammate puuid -> [wins, games, name]
    glen = defaultdict(lambda: [0, 0])       # length bucket -> [wins, games]
    throw = [0, 0]                            # [throws, eligible-ahead-games]
    comeback = [0, 0]                         # [comebacks, eligible-behind-games]
    ff_lost = ff_won = 0

    for fn in os.listdir(MDIR):
        m = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))["info"]
        if m.get("queueId") != 420:
            continue
        me = next((p for p in m["participants"] if p["puuid"] == ME), None)
        if not me or me.get("teamPosition") != "BOTTOM":
            continue
        win = bool(me.get("win"))
        tid = me["teamId"]

        s = next((p for p in m["participants"]
                  if p["teamId"] == tid and p.get("teamPosition") == "UTILITY"), None)
        if s:
            sup[s["championName"]][1] += 1
            sup[s["championName"]][0] += win

        for p in m["participants"]:
            if p["teamId"] == tid and p["puuid"] != ME:
                d = mate[p["puuid"]]
                d[1] += 1
                d[0] += win
                d[2] = p.get("riotIdGameName") or "?"

        mins = (m.get("gameDuration") or 0) / 60
        b = "<25 min" if mins < 25 else ("25–32 min" if mins < 32 else "32+ min")
        glen[b][1] += 1
        glen[b][0] += win

        if me.get("gameEndedInSurrender"):
            ff_won += win
            ff_lost += (not win)

        tp = os.path.join(TDIR, fn)
        if os.path.exists(tp):
            frames = json.load(open(tp, encoding="utf-8"))["info"]["frames"]
            if len(frames) > 15:
                pf = frames[15]["participantFrames"]
                mine = sum(pf[str(i)]["totalGold"] for i in (range(1, 6) if tid == 100 else range(6, 11)))
                opp = sum(pf[str(i)]["totalGold"] for i in (range(6, 11) if tid == 100 else range(1, 6)))
                lead = mine - opp
                if lead > 2000:
                    throw[1] += 1
                    throw[0] += (not win)
                elif lead < -2000:
                    comeback[1] += 1
                    comeback[0] += win

    support = sorted(
        [{"champion": c, "games": g, "wins": w, "wr": wr(w, g)}
         for c, (w, g) in sup.items() if g >= 12],
        key=lambda x: x["wr"])
    squad = sorted(
        [{"name": d[2], "games": d[1], "wins": d[0], "wr": wr(d[0], d[1])}
         for d in mate.values() if d[1] >= 5],
        key=lambda x: -x["games"])
    length = [{"bucket": b, "games": glen[b][1], "wins": glen[b][0], "wr": wr(*glen[b][::-1])}
              for b in ["<25 min", "25–32 min", "32+ min"] if glen[b][1]]

    social = {
        "support": support,
        "squad": squad,
        "gameLength": length,
        "throw": {"eligible": throw[1], "count": throw[0], "rate": wr(throw[0], throw[1])},
        "comeback": {"eligible": comeback[1], "count": comeback[0], "rate": wr(comeback[0], comeback[1])},
        "surrender": {"ffAndLost": ff_lost, "wonVsFf": ff_won},
    }

    apath = os.path.join(OUT, "analysis.json")
    A = json.load(open(apath, encoding="utf-8"))
    A["social"] = social
    json.dump(A, open(apath, "w", encoding="utf-8"), indent=2)
    print("support pairings:", len(support), "| squad members:", len(squad))
    print("best support:", support[-1], "| worst:", support[0])
    print("top duo:", max(squad, key=lambda x: x["games"]))
    print("throw rate:", social["throw"], "| comeback:", social["comeback"])


if __name__ == "__main__":
    main()
