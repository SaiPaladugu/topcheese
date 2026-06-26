"""
Duo analysis: how does playing alongside 'Calatis' (across his alt accounts)
affect Topcheese044's games? Pure local pass over data/raw/matches; merges a
"duo" block into data/processed/analysis.json for the dashboard + report.
"""
import os
import json
import statistics as st
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
OUT = os.path.join(HERE, "data", "processed")
ME = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"
PARTNER = "calatis"  # match on riotIdGameName, case-insensitive


def me_metrics(p, info):
    ch = p.get("challenges", {})
    dur = (info.get("gameDuration") or 1) / 60.0
    cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
    return {
        "win": int(bool(p.get("win"))),
        "kda": ch.get("kda", 0.0),
        "csPerMin": cs / dur if dur else 0,
        "kp": ch.get("killParticipation", 0.0) * 100,
        "teamDmgPct": ch.get("teamDamagePercentage", 0.0) * 100,
        "deaths": p.get("deaths", 0),
        "dragonTakedowns": ch.get("dragonTakedowns", 0),
        "champion": p.get("championName"),
    }


def avg(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return round(st.mean(v), 2) if v else None


def main():
    accounts = Counter()          # any queue, for "how often they're queued up" context
    cal_roles = Counter()         # ranked-solo only
    cal_champs = Counter()        # ranked-solo only
    cal_self = []                 # calatis's own perf, ranked-solo duo games
    together, alone = [], []      # ranked-solo (420) ONLY -> fair comparison
    per_account = defaultdict(lambda: {"games": 0, "wins": 0})  # ranked-solo
    shared_any = 0

    for fn in os.listdir(MDIR):
        info = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))["info"]
        me = next((p for p in info["participants"] if p["puuid"] == ME), None)
        if not me:
            continue
        cal = next((p for p in info["participants"]
                    if (p.get("riotIdGameName") or "").lower() == PARTNER), None)
        if cal and cal.get("teamId") == me.get("teamId"):
            shared_any += 1
            accounts[f"{cal.get('riotIdGameName')}#{cal.get('riotIdTagline')}"] += 1

        # ---- core comparison restricted to ranked solo (queue 420) ----
        if info.get("queueId") != 420:
            continue
        mm = me_metrics(me, info)
        if cal and cal.get("teamId") == me.get("teamId"):
            together.append(mm)
            acct = f"{cal.get('riotIdGameName')}#{cal.get('riotIdTagline')}"
            per_account[acct]["games"] += 1
            per_account[acct]["wins"] += mm["win"]
            cal_roles[cal.get("teamPosition") or "?"] += 1
            cal_champs[cal.get("championName")] += 1
            cdur = (info.get("gameDuration") or 1) / 60.0
            ccs = cal.get("totalMinionsKilled", 0) + cal.get("neutralMinionsKilled", 0)
            cch = cal.get("challenges", {})
            cal_self.append({"win": mm["win"], "kda": cch.get("kda", 0.0),
                             "kp": cch.get("killParticipation", 0.0) * 100,
                             "csPerMin": ccs / cdur if cdur else 0,
                             "deaths": cal.get("deaths", 0)})
        else:
            alone.append(mm)

    def wr(rows):
        return round(100 * sum(r["win"] for r in rows) / len(rows), 1) if rows else None

    duo = {
        "partner": "Calatis",
        "note": "Core comparison is ranked solo/duo (queue 420) only, for a fair apples-to-apples read.",
        "sharedGamesAnyQueue": shared_any,
        "accounts": [{"id": a, "games": n} for a, n in accounts.most_common()],
        "together": {"games": len(together), "wr": wr(together)},
        "alone": {"games": len(alone), "wr": wr(alone)},
        "perAccount": [
            {"id": a, "games": d["games"], "wins": d["wins"],
             "wr": round(100 * d["wins"] / d["games"], 1) if d["games"] else None}
            for a, d in sorted(per_account.items(), key=lambda x: -x[1]["games"])
        ],
        "hisStatsTogether": {k: avg(together, k) for k in
                             ["kda", "csPerMin", "kp", "teamDmgPct", "deaths", "dragonTakedowns"]},
        "hisStatsAlone": {k: avg(alone, k) for k in
                          ["kda", "csPerMin", "kp", "teamDmgPct", "deaths", "dragonTakedowns"]},
        "calatisRoles": dict(cal_roles.most_common()),
        "calatisChamps": cal_champs.most_common(6),
        "calatisSelf": {
            "wr": wr(cal_self),
            "kda": avg(cal_self, "kda"), "kp": avg(cal_self, "kp"),
            "csPerMin": avg(cal_self, "csPerMin"), "deaths": avg(cal_self, "deaths"),
        },
    }

    apath = os.path.join(OUT, "analysis.json")
    A = json.load(open(apath, encoding="utf-8"))
    A["duo"] = duo
    json.dump(A, open(apath, "w", encoding="utf-8"), indent=2)

    print(json.dumps(duo, indent=2))


if __name__ == "__main__":
    main()
