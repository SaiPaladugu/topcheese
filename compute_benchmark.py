"""
Close Stage 1.5: compute the Diamond-ADC baseline from our sampled benchmark
dataset and put Topcheese044 head-to-head against it. Local-only.
"""
import os
import json
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
BM = os.path.join(HERE, "data", "benchmark")
RAW = os.path.join(HERE, "data", "raw")
ME_PUUID = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"


def frame_cs_gold(tl, pid, minute):
    frames = tl.get("info", {}).get("frames", [])
    if minute >= len(frames):
        return None
    pf = frames[minute].get("participantFrames", {}).get(str(pid))
    if not pf:
        return None
    cs = pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0)
    return pf.get("totalGold", 0), cs


def metrics_from(match, tl, puuid):
    """Return a dict of ADC metrics for `puuid` in this match, or None."""
    info = match["info"]
    p = next((x for x in info["participants"] if x["puuid"] == puuid), None)
    if not p or p.get("teamPosition") != "BOTTOM":
        return None
    ch = p.get("challenges", {})
    dur = (info.get("gameDuration") or 1) / 60.0
    cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
    # lane diff @14 vs enemy ADC
    opp = next((x for x in info["participants"]
                if x.get("teamId") != p["teamId"] and x.get("teamPosition") == "BOTTOM"), None)
    g14 = c14 = None
    if opp and tl:
        a = frame_cs_gold(tl, p["participantId"], 14)
        b = frame_cs_gold(tl, opp["participantId"], 14)
        if a and b:
            g14, c14 = a[0] - b[0], a[1] - b[1]
    return {
        "win": int(bool(p.get("win"))),
        "csPerMin": cs / dur,
        "deaths": p.get("deaths", 0),
        "deadPct": 100 * p.get("totalTimeSpentDead", 0) / (info.get("gameDuration") or 1),
        "kda": ch.get("kda", 0),
        "kp": ch.get("killParticipation", 0) * 100,
        "teamDmgPct": ch.get("teamDamagePercentage", 0) * 100,
        "dmgPerMin": ch.get("damagePerMinute", 0),
        "goldPerMin": ch.get("goldPerMinute", 0),
        "visionPerMin": ch.get("visionScorePerMinute", 0),
        "controlWards": ch.get("controlWardsPlaced", 0),
        "soloKills": ch.get("soloKills", 0),
        "laneMinions10": ch.get("laneMinionsFirst10Minutes", 0),
        "laneGoldExpAdv": ch.get("laningPhaseGoldExpAdvantage", 0),
        "goldDiff14": g14,
        "csDiff14": c14,
    }


def collect(index_pairs, mdir, tdir):
    out = []
    for matchId, puuid in index_pairs:
        mp = os.path.join(mdir, f"{matchId}.json")
        if not os.path.exists(mp):
            continue
        match = json.load(open(mp, encoding="utf-8"))
        tp = os.path.join(tdir, f"{matchId}.json")
        tl = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else None
        r = metrics_from(match, tl, puuid)
        if r:
            out.append(r)
    return out


def agg(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return (st.mean(vals), st.median(vals)) if vals else (None, None)


def main():
    # benchmark cohort
    idx = json.load(open(os.path.join(BM, "adc_index.json"), encoding="utf-8"))
    bench = collect([(d["matchId"], d["puuid"]) for d in idx],
                    os.path.join(BM, "matches"), os.path.join(BM, "timelines"))
    # his own ADC games (reuse raw)
    me_pairs = []
    for fn in os.listdir(os.path.join(RAW, "matches")):
        mid = fn[:-5]
        me_pairs.append((mid, ME_PUUID))
    mine = collect(me_pairs, os.path.join(RAW, "matches"), os.path.join(RAW, "timelines"))

    print(f"Cohort: him={len(mine)} ADC games | Diamond benchmark={len(bench)} ADC games\n")
    cols = [
        ("csPerMin", "CS / min", "+"), ("laneMinions10", "Lane CS @10", "+"),
        ("goldDiff14", "Gold diff @14", "+"), ("csDiff14", "CS diff @14", "+"),
        ("laneGoldExpAdv", "Laning gold/xp adv", "+"),
        ("teamDmgPct", "Team dmg %", "+"), ("dmgPerMin", "Damage / min", "+"),
        ("kp", "Kill participation %", "+"), ("kda", "KDA", "+"),
        ("deaths", "Deaths / game", "-"), ("deadPct", "Time dead %", "-"),
        ("soloKills", "Solo kills", "+"), ("goldPerMin", "Gold / min", "+"),
        ("visionPerMin", "Vision / min", "+"), ("controlWards", "Control wards", "+"),
    ]
    print(f"{'Metric':<22}{'Him (mean)':>12}{'Diamond':>12}{'Delta':>12}  flag")
    print("-" * 72)
    for key, label, good in cols:
        hm, _ = agg(mine, key)
        bm, _ = agg(bench, key)
        if hm is None or bm is None:
            continue
        delta = hm - bm
        better = (delta >= 0) if good == "+" else (delta <= 0)
        flag = "ok" if better else "<<<"
        print(f"{label:<22}{hm:>12.2f}{bm:>12.2f}{delta:>+12.2f}  {flag}")

    hw = st.mean([r["win"] for r in mine]) * 100
    bw = st.mean([r["win"] for r in bench]) * 100
    print("-" * 72)
    print(f"{'Win rate %':<22}{hw:>12.1f}{bw:>12.1f}")


if __name__ == "__main__":
    main()
