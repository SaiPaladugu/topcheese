"""
Duo analysis: how do specific friends (each amalgamated across their alt accounts)
affect Topcheese044's ranked games? Pure local pass over data/raw/matches.

People are matched by riotIdGameName so all of a person's alts roll up into one:
  - Calatis  = Calatis#uwu / #zoe / #owo
  - Tony     = ernump (#NA1) + chaewon
Merges per-person blocks into analysis.json: "duo" (Calatis, kept for the Calatis
section) and "tony".
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

PEOPLE = {
    "Calatis": {"gameNames": {"calatis"}},
    "Tony": {"gameNames": {"ernump", "chaewon"}},
}


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
    }


def avg(rows, k):
    v = [r[k] for r in rows if r.get(k) is not None]
    return round(st.mean(v), 2) if v else None


def wr(rows):
    return round(100 * sum(r["win"] for r in rows) / len(rows), 1) if rows else None


def analyze(person, names):
    accounts = Counter()      # any queue, "how often queued up"
    roles = Counter()
    champs = Counter()
    self_perf = []            # the friend's own perf, ranked-solo duo games
    together, alone = [], []  # ranked-solo (420) only
    per_account = defaultdict(lambda: {"games": 0, "wins": 0})
    shared_any = 0

    for fn in os.listdir(MDIR):
        info = json.load(open(os.path.join(MDIR, fn), encoding="utf-8"))["info"]
        me = next((p for p in info["participants"] if p["puuid"] == ME), None)
        if not me:
            continue
        friend = next((p for p in info["participants"]
                       if (p.get("riotIdGameName") or "").lower() in names
                       and p.get("teamId") == me.get("teamId")), None)
        if friend:
            shared_any += 1
            accounts[f"{friend.get('riotIdGameName')}#{friend.get('riotIdTagline')}"] += 1

        if info.get("queueId") != 420:
            continue
        mm = me_metrics(me, info)
        if friend:
            together.append(mm)
            acct = f"{friend.get('riotIdGameName')}#{friend.get('riotIdTagline')}"
            per_account[acct]["games"] += 1
            per_account[acct]["wins"] += mm["win"]
            roles[friend.get("teamPosition") or "?"] += 1
            champs[friend.get("championName")] += 1
            cdur = (info.get("gameDuration") or 1) / 60.0
            ccs = friend.get("totalMinionsKilled", 0) + friend.get("neutralMinionsKilled", 0)
            cch = friend.get("challenges", {})
            self_perf.append({"win": mm["win"], "kda": cch.get("kda", 0.0),
                              "kp": cch.get("killParticipation", 0.0) * 100,
                              "csPerMin": ccs / cdur if cdur else 0,
                              "deaths": friend.get("deaths", 0),
                              "teamDmgPct": cch.get("teamDamagePercentage", 0.0) * 100})
        else:
            alone.append(mm)

    return {
        "partner": person,
        "note": "Ranked solo/duo (queue 420), all of this person's alt accounts amalgamated.",
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
        "partnerRoles": dict(roles.most_common()),
        "partnerChamps": champs.most_common(6),
        "partnerSelf": {
            "wr": wr(self_perf), "kda": avg(self_perf, "kda"), "kp": avg(self_perf, "kp"),
            "csPerMin": avg(self_perf, "csPerMin"), "deaths": avg(self_perf, "deaths"),
            "teamDmgPct": avg(self_perf, "teamDmgPct"),
        },
    }


def main():
    blocks = {name: analyze(name, cfg["gameNames"]) for name, cfg in PEOPLE.items()}
    apath = os.path.join(OUT, "analysis.json")
    A = json.load(open(apath, encoding="utf-8"))
    A["duo"] = blocks["Calatis"]      # the Calatis section reads this
    A["tony"] = blocks["Tony"]
    json.dump(A, open(apath, "w", encoding="utf-8"), indent=2)
    for name, b in blocks.items():
        print(f"\n=== {name} ({b['sharedGamesAnyQueue']} shared, accts {[a['id'] for a in b['accounts']]}) ===")
        print(f"  together: {b['together']}  | alone: {b['alone']}")
        print(f"  per-account: {b['perAccount']}")
        print(f"  {name}'s own: {b['partnerSelf']}  roles {b['partnerRoles']}")


if __name__ == "__main__":
    main()
