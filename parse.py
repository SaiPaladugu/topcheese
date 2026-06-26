"""
Stage 1 -> Stage 2 bridge: flatten Topcheese044's ranked-solo (queue 420) games
into one tidy table (data/processed/ranked_solo.csv), combining match-detail
fields, the rich `challenges` metrics, and timeline-derived lane diffs vs his
direct lane opponent at 10 and 14 minutes.

Local-only (no API). Run after fetch.py.
"""
import os
import json
import csv

PUUID = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
TDIR = os.path.join(RAW, "timelines")
OUT = os.path.join(HERE, "data", "processed")
os.makedirs(OUT, exist_ok=True)

OPP_POS = {  # his position -> the enemy position that opposes him
    "BOTTOM": "BOTTOM", "UTILITY": "UTILITY", "MIDDLE": "MIDDLE",
    "TOP": "TOP", "JUNGLE": "JUNGLE",
}


def frame_stats(timeline, pid, minute):
    """Return (totalGold, totalCs, xp) for participant pid at ~minute, or None."""
    frames = timeline.get("info", {}).get("frames", [])
    if minute >= len(frames):
        return None
    pf = frames[minute].get("participantFrames", {}).get(str(pid))
    if not pf:
        return None
    cs = pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0)
    return pf.get("totalGold", 0), cs, pf.get("xp", 0)


def lane_diff(timeline, my_pid, opp_pid, minute):
    me = frame_stats(timeline, my_pid, minute)
    op = frame_stats(timeline, opp_pid, minute)
    if not me or not op:
        return (None, None, None)
    return (me[0] - op[0], me[1] - op[1], me[2] - op[2])  # gold, cs, xp diffs


def main():
    rows = []
    for fn in os.listdir(MDIR):
        m = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))
        info = m["info"]
        if info.get("queueId") != 420:
            continue
        me = next((p for p in info["participants"] if p["puuid"] == PUUID), None)
        if not me:
            continue
        ch = me.get("challenges", {})
        dur_min = (info.get("gameDuration") or 0) / 60.0
        cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
        mid = m["metadata"]["matchId"]

        # find direct lane opponent (enemy team, same teamPosition)
        my_pos = me.get("teamPosition", "")
        opp = None
        if my_pos:
            opp = next((p for p in info["participants"]
                        if p.get("teamId") != me["teamId"]
                        and p.get("teamPosition") == OPP_POS.get(my_pos, my_pos)), None)

        # timeline lane diffs at 10 and 14 min
        g10 = c10 = x10 = g14 = c14 = x14 = None
        tpath = os.path.join(TDIR, f"{mid}.json")
        if opp and os.path.exists(tpath):
            tl = json.load(open(tpath, encoding="utf-8"))
            g10, c10, x10 = lane_diff(tl, me["participantId"], opp["participantId"], 10)
            g14, c14, x14 = lane_diff(tl, me["participantId"], opp["participantId"], 14)

        rows.append({
            "matchId": mid,
            "date": info.get("gameCreation", 0) // 1000,
            "patch": info.get("gameVersion", "").rsplit(".", 2)[0] if info.get("gameVersion") else "",
            "durationMin": round(dur_min, 1),
            "champion": me.get("championName"),
            "position": my_pos,
            "win": int(bool(me.get("win"))),
            "kills": me.get("kills"), "deaths": me.get("deaths"), "assists": me.get("assists"),
            "kda": round(ch.get("kda", 0), 2),
            "cs": cs,
            "csPerMin": round(cs / dur_min, 2) if dur_min else 0,
            "goldPerMin": round(ch.get("goldPerMinute", 0), 1),
            "dmgPerMin": round(ch.get("damagePerMinute", 0), 1),
            "teamDmgPct": round(ch.get("teamDamagePercentage", 0) * 100, 1),
            "killParticipation": round(ch.get("killParticipation", 0) * 100, 1),
            "visionPerMin": round(ch.get("visionScorePerMinute", 0), 2),
            "controlWards": ch.get("controlWardsPlaced", 0),
            "soloKills": ch.get("soloKills", 0),
            "timeDeadSec": me.get("totalTimeSpentDead", 0),
            "deadPct": round(100 * me.get("totalTimeSpentDead", 0) / (info.get("gameDuration") or 1), 1),
            "laneMinions10": ch.get("laneMinionsFirst10Minutes", 0),
            "laneGoldExpAdv": round(ch.get("laningPhaseGoldExpAdvantage", 0), 2),
            "earlyLaneAdv": round(ch.get("earlyLaningPhaseGoldExpAdvantage", 0), 2),
            "maxCsAdvOpp": round(ch.get("maxCsAdvantageOnLaneOpponent", 0), 1),
            "visionAdvOpp": round(ch.get("visionScoreAdvantageLaneOpponent", 0), 2),
            "goldDiff10": g10, "csDiff10": c10, "xpDiff10": x10,
            "goldDiff14": g14, "csDiff14": c14, "xpDiff14": x14,
            "firstTowerKilledTime": round(ch.get("firstTurretKilledTime", 0), 0),
            "turretPlates": ch.get("turretPlatesTaken", 0),
            "doubleKills": me.get("doubleKills"), "tripleKills": me.get("tripleKills"),
            "quadraKills": me.get("quadraKills"), "pentaKills": me.get("pentaKills"),
            "surrenderEnd": int(bool(me.get("gameEndedInSurrender"))),
            "earlySurrender": int(bool(me.get("gameEndedInEarlySurrender"))),
        })

    rows.sort(key=lambda r: r["date"])
    out_csv = os.path.join(OUT, "ranked_solo.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} ranked-solo games -> {out_csv}")

    # quick sanity summary
    wins = sum(r["win"] for r in rows)
    have_tl = sum(1 for r in rows if r["goldDiff14"] is not None)
    print(f"  WR: {wins}/{len(rows)} = {100*wins/len(rows):.1f}%")
    print(f"  games with timeline @14 lane diff: {have_tl}")
    avg = lambda k: sum(r[k] for r in rows) / len(rows)
    print(f"  avg cs/min {avg('csPerMin'):.2f} | deaths {avg('deaths'):.2f} | "
          f"dead% {avg('deadPct'):.1f} | KP {avg('killParticipation'):.1f}% | "
          f"teamDmg% {avg('teamDmgPct'):.1f} | vision/min {avg('visionPerMin'):.2f}")


if __name__ == "__main__":
    main()
