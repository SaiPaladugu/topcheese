"""
Stage 2 analysis engine for Topcheese044#NA1 ranked-solo (queue 420).

One clean pass over raw match details + timelines builds a rich per-game record,
then computes:
  - win-vs-loss differentials (mean in wins vs losses + Cohen's d effect size)
  - per-champion deep dive (WR, KDA, farm, impact, lane diffs)
  - enemy-ADC matchup win rates (overall + for his signature champs)
  - tilt / session / streak / time-of-day patterns (timezone inferred from data)
  - recent-form rolling win rate
  - death-timing analysis from timelines

Writes data/processed/analysis.json (machine-readable for the website + report).
Local-only, no API.
"""
import os
import json
import math
import datetime as dt
from collections import defaultdict, Counter

import numpy as np

PUUID = "YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA"
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MDIR = os.path.join(RAW, "matches")
TDIR = os.path.join(RAW, "timelines")
BM = os.path.join(HERE, "data", "benchmark")
OUT = os.path.join(HERE, "data", "processed")
os.makedirs(OUT, exist_ok=True)


# ---------- timeline helpers ----------
def pframe(tl, pid, minute):
    frames = tl.get("info", {}).get("frames", [])
    if minute >= len(frames):
        return None
    return frames[minute].get("participantFrames", {}).get(str(pid))


def cs_gold_xp(pf):
    if not pf:
        return None
    return (pf.get("totalGold", 0),
            pf.get("minionsKilled", 0) + pf.get("jungleMinionsKilled", 0),
            pf.get("xp", 0))


def my_death_minutes(tl, my_pid):
    """List of minute-marks where my_pid died (from CHAMPION_KILL events)."""
    out = []
    for fr in tl.get("info", {}).get("frames", []):
        for ev in fr.get("events", []):
            if ev.get("type") == "CHAMPION_KILL" and ev.get("victimId") == my_pid:
                out.append(ev.get("timestamp", 0) / 60000.0)
    return out


# ---------- build rich per-game records ----------
def build_records(match_dir, timeline_dir, puuid, solo_only=True):
    recs = []
    for fn in os.listdir(match_dir):
        m = json.load(open(os.path.join(match_dir, fn), encoding="utf-8"))
        info = m["info"]
        if solo_only and info.get("queueId") != 420:
            continue
        me = next((p for p in info["participants"] if p["puuid"] == puuid), None)
        if not me:
            continue
        ch = me.get("challenges", {})
        dur = (info.get("gameDuration") or 1)
        dur_min = dur / 60.0
        cs = me.get("totalMinionsKilled", 0) + me.get("neutralMinionsKilled", 0)
        mid = m["metadata"]["matchId"]
        pos = me.get("teamPosition", "")

        # lane opponent (enemy same position)
        opp = next((p for p in info["participants"]
                    if p.get("teamId") != me["teamId"] and p.get("teamPosition") == pos and pos),
                   None)
        enemy_adc = next((p for p in info["participants"]
                          if p.get("teamId") != me["teamId"] and p.get("teamPosition") == "BOTTOM"),
                         None)

        g10 = c10 = g14 = c14 = x14 = None
        first_death = None
        deaths_before10 = deaths_before15 = None
        tpath = os.path.join(timeline_dir, f"{mid}.json")
        if os.path.exists(tpath):
            tl = json.load(open(tpath, encoding="utf-8"))
            if opp:
                a10, b10 = cs_gold_xp(pframe(tl, me["participantId"], 10)), cs_gold_xp(pframe(tl, opp["participantId"], 10))
                a14, b14 = cs_gold_xp(pframe(tl, me["participantId"], 14)), cs_gold_xp(pframe(tl, opp["participantId"], 14))
                if a10 and b10:
                    g10, c10 = a10[0] - b10[0], a10[1] - b10[1]
                if a14 and b14:
                    g14, c14, x14 = a14[0] - b14[0], a14[1] - b14[1], a14[2] - b14[2]
            dmins = my_death_minutes(tl, me["participantId"])
            if dmins:
                first_death = min(dmins)
            deaths_before10 = sum(1 for d in dmins if d <= 10)
            deaths_before15 = sum(1 for d in dmins if d <= 15)

        recs.append({
            "matchId": mid,
            "ts": info.get("gameCreation", 0) // 1000,  # epoch seconds
            "patch": ".".join(info.get("gameVersion", "").split(".")[:2]),
            "durationMin": round(dur_min, 2),
            "champion": me.get("championName"),
            "position": pos,
            "win": int(bool(me.get("win"))),
            "kills": me.get("kills", 0), "deaths": me.get("deaths", 0), "assists": me.get("assists", 0),
            "kda": ch.get("kda", 0.0),
            "cs": cs, "csPerMin": cs / dur_min if dur_min else 0,
            "goldPerMin": ch.get("goldPerMinute", 0.0),
            "dmgPerMin": ch.get("damagePerMinute", 0.0),
            "teamDmgPct": ch.get("teamDamagePercentage", 0.0) * 100,
            "kp": ch.get("killParticipation", 0.0) * 100,
            "visionPerMin": ch.get("visionScorePerMinute", 0.0),
            "controlWards": ch.get("controlWardsPlaced", 0),
            "soloKills": ch.get("soloKills", 0),
            "deadPct": 100 * me.get("totalTimeSpentDead", 0) / dur,
            "laneMinions10": ch.get("laneMinionsFirst10Minutes", 0),
            "laneGoldExpAdv": ch.get("laningPhaseGoldExpAdvantage", 0.0),
            "earlyLaneAdv": ch.get("earlyLaningPhaseGoldExpAdvantage", 0.0),
            "turretPlates": ch.get("turretPlatesTaken", 0),
            "objectivesStolen": me.get("objectivesStolen", 0),
            "dragonTakedowns": ch.get("dragonTakedowns", 0),
            "baronTakedowns": ch.get("baronTakedowns", 0),
            "riftHeraldTakedowns": ch.get("riftHeraldTakedowns", 0),
            "goldDiff10": g10, "csDiff10": c10,
            "goldDiff14": g14, "csDiff14": c14, "xpDiff14": x14,
            "firstDeathMin": first_death,
            "deathsBefore10": deaths_before10, "deathsBefore15": deaths_before15,
            "enemyAdc": enemy_adc.get("championName") if enemy_adc else None,
            "surrender": int(bool(me.get("gameEndedInSurrender"))),
            "remake": int(bool(me.get("gameEndedInEarlySurrender"))),
        })
    recs.sort(key=lambda r: r["ts"])
    return recs


# ---------- stats helpers ----------
def cohens_d(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) < 2 or len(b) < 2:
        return None
    na, nb = len(a), len(b)
    sp = math.sqrt(((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2))
    if sp == 0:
        return 0.0
    return (a.mean() - b.mean()) / sp


def vals(recs, key):
    return [r[key] for r in recs if r.get(key) is not None]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


# ---------- analyses ----------
def win_loss_diff(recs):
    wins = [r for r in recs if r["win"]]
    losses = [r for r in recs if not r["win"]]
    metrics = [
        ("kp", "Kill participation %", "+"),
        ("teamDmgPct", "Team damage share %", "+"),
        ("dmgPerMin", "Damage / min", "+"),
        ("goldPerMin", "Gold / min", "+"),
        ("goldDiff14", "Gold diff vs lane @14", "+"),
        ("csDiff14", "CS diff vs lane @14", "+"),
        ("xpDiff14", "XP diff vs lane @14", "+"),
        ("csPerMin", "CS / min", "+"),
        ("laneMinions10", "Lane CS @10", "+"),
        ("deaths", "Deaths", "-"),
        ("deadPct", "Time dead %", "-"),
        ("deathsBefore15", "Deaths before 15min", "-"),
        ("firstDeathMin", "First death (min, later=better)", "+"),
        ("kda", "KDA", "+"),
        ("visionPerMin", "Vision / min", "+"),
        ("controlWards", "Control wards", "+"),
        ("soloKills", "Solo kills", "+"),
        ("turretPlates", "Turret plates", "+"),
        ("dragonTakedowns", "Dragon takedowns", "+"),
        ("durationMin", "Game length (min)", "0"),
    ]
    rows = []
    for key, label, direction in metrics:
        wm, lm = mean(vals(wins, key)), mean(vals(losses, key))
        if wm is None or lm is None:
            continue
        d = cohens_d(vals(wins, key), vals(losses, key))
        rows.append({"key": key, "label": label, "direction": direction,
                     "winMean": round(wm, 2), "lossMean": round(lm, 2),
                     "delta": round(wm - lm, 2),
                     "cohensD": round(d, 3) if d is not None else None})
    # rank by absolute effect size
    rows.sort(key=lambda r: abs(r["cohensD"]) if r["cohensD"] is not None else 0, reverse=True)
    return rows


def per_champion(recs, min_games=5):
    by = defaultdict(list)
    for r in recs:
        by[r["champion"]].append(r)
    out = []
    for champ, rs in by.items():
        n = len(rs)
        w = sum(x["win"] for x in rs)
        out.append({
            "champion": champ, "games": n, "wins": w, "wr": round(100 * w / n, 1),
            "kda": round(mean(vals(rs, "kda")), 2),
            "csPerMin": round(mean(vals(rs, "csPerMin")), 2),
            "kp": round(mean(vals(rs, "kp")), 1),
            "teamDmgPct": round(mean(vals(rs, "teamDmgPct")), 1),
            "dmgPerMin": round(mean(vals(rs, "dmgPerMin")), 0),
            "goldDiff14": round(mean(vals(rs, "goldDiff14")) or 0, 0),
            "deaths": round(mean(vals(rs, "deaths")), 2),
            "share": round(100 * n / len(recs), 1),
        })
    out.sort(key=lambda c: c["games"], reverse=True)
    return out


def matchups(recs, min_games=6):
    # his WR by enemy ADC champion (overall)
    by_enemy = defaultdict(list)
    for r in recs:
        if r["enemyAdc"]:
            by_enemy[r["enemyAdc"]].append(r["win"])
    overall = [{"enemyAdc": k, "games": len(v), "wins": sum(v), "wr": round(100 * sum(v) / len(v), 1)}
               for k, v in by_enemy.items() if len(v) >= min_games]
    overall.sort(key=lambda x: x["wr"])
    # his signature champs vs enemy ADC
    by_pair = defaultdict(list)
    for r in recs:
        if r["enemyAdc"]:
            by_pair[(r["champion"], r["enemyAdc"])].append(r["win"])
    pairs = [{"champion": c, "enemyAdc": e, "games": len(v), "wins": sum(v),
              "wr": round(100 * sum(v) / len(v), 1)}
             for (c, e), v in by_pair.items() if len(v) >= min_games]
    pairs.sort(key=lambda x: (x["champion"], x["wr"]))
    return {"byEnemyAdc": overall, "byPair": pairs}


def infer_utc_offset(recs):
    """Infer his local UTC offset by finding his least-active 5h window (sleep),
    assuming its center sits at ~05:00 local."""
    hours = Counter()
    for r in recs:
        hours[dt.datetime.fromtimestamp(r["ts"], dt.timezone.utc).hour] += 1
    counts = [hours.get(h, 0) for h in range(24)]
    best_h, best_sum = 0, 1e9
    for start in range(24):
        s = sum(counts[(start + i) % 24] for i in range(5))
        if s < best_sum:
            best_sum, best_h = s, start
    sleep_center_utc = (best_h + 2) % 24       # center of the 5h trough, in UTC
    offset = (5 - sleep_center_utc)             # want center at 05:00 local
    if offset > 0:
        offset -= 24
    return offset, best_sum


def time_patterns(recs):
    offset, trough = infer_utc_offset(recs)

    def local(ts):
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc) + dt.timedelta(hours=offset)

    # sessions: gap < 3h => same session; index of game within session
    SESS_GAP = 3 * 3600
    sessions = []
    cur = []
    for r in recs:
        if cur and r["ts"] - cur[-1]["ts"] > SESS_GAP:
            sessions.append(cur); cur = []
        cur.append(r)
    if cur:
        sessions.append(cur)

    by_session_game = defaultdict(list)   # 1st/2nd/.../5+ game of a session
    for sess in sessions:
        for i, r in enumerate(sess):
            bucket = min(i + 1, 5)
            by_session_game[bucket].append(r["win"])

    # streak state immediately before each game
    by_streak = defaultdict(list)
    for i, r in enumerate(recs):
        # look back within same session day? use raw consecutive sequence
        streak = 0; sign = None
        j = i - 1
        while j >= 0:
            wj = recs[j]["win"]
            if sign is None:
                sign = wj
                streak = 1
            elif wj == sign:
                streak += 1
            else:
                break
            j -= 1
        if sign is None:
            label = "first game"
        else:
            cap = min(streak, 3)
            label = f"after {cap}{'+' if streak > 3 else ''} {'win' if sign else 'loss'}{'es' if (sign==0 and cap>1) else ('s' if (sign==1 and cap>1) else '')}"
        by_streak[label].append(r["win"])

    # games per (local) day
    by_day = defaultdict(list)
    for r in recs:
        by_day[local(r["ts"]).date().isoformat()].append(r["win"])
    gpd_bucket = defaultdict(list)  # bucket: how WR varies by how many games that day
    for day, ws in by_day.items():
        n = len(ws)
        b = "1-2" if n <= 2 else ("3-5" if n <= 5 else ("6-9" if n <= 9 else "10+"))
        for w in ws:
            gpd_bucket[b].append(w)

    # hour of day (local)
    by_hour = defaultdict(list)
    for r in recs:
        by_hour[local(r["ts"]).hour].append(r["win"])

    # weekday (local)
    by_weekday = defaultdict(list)
    wd_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for r in recs:
        by_weekday[wd_names[local(r["ts"]).weekday()]].append(r["win"])

    def pack(d, order=None):
        items = []
        keys = order if order else sorted(d.keys())
        for k in keys:
            if k in d and len(d[k]):
                v = d[k]
                items.append({"bucket": str(k), "games": len(v), "wins": sum(v),
                              "wr": round(100 * sum(v) / len(v), 1)})
        return items

    streak_order = ["after 3+ losses", "after 2 losses", "after 1 loss", "first game",
                    "after 1 win", "after 2 wins", "after 3+ wins"]
    return {
        "inferredUtcOffset": offset,
        "nSessions": len(sessions),
        "avgSessionLen": round(sum(len(s) for s in sessions) / len(sessions), 2),
        "bySessionGame": pack(by_session_game, [1, 2, 3, 4, 5]),
        "byStreak": pack(by_streak, streak_order),
        "byGamesPerDay": pack(gpd_bucket, ["1-2", "3-5", "6-9", "10+"]),
        "byHour": pack(by_hour, list(range(24))),
        "byWeekday": pack(by_weekday, wd_names),
    }


def recent_form(recs, window=50):
    out = []
    wins = [r["win"] for r in recs]
    for i in range(len(recs)):
        lo = max(0, i - window + 1)
        seg = wins[lo:i + 1]
        out.append({"i": i, "ts": recs[i]["ts"],
                    "rollingWR": round(100 * sum(seg) / len(seg), 1)})
    return out


def benchmark_block():
    """Reuse benchmark cohort to compute Diamond ADC means for key metrics."""
    idx_path = os.path.join(BM, "adc_index.json")
    if not os.path.exists(idx_path):
        return None
    idx = json.load(open(idx_path, encoding="utf-8"))
    bench = build_records(os.path.join(BM, "matches"),
                          os.path.join(BM, "timelines"), None, solo_only=False) \
        if False else None
    # build per (matchId,puuid) directly
    rows = []
    for d in idx:
        mp = os.path.join(BM, "matches", f"{d['matchId']}.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp, encoding="utf-8"))
        info = m["info"]
        p = next((x for x in info["participants"] if x["puuid"] == d["puuid"]), None)
        if not p:
            continue
        ch = p.get("challenges", {})
        dur = (info.get("gameDuration") or 1)
        cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
        rows.append({
            "win": int(bool(p.get("win"))),
            "csPerMin": cs / (dur / 60.0),
            "kp": ch.get("killParticipation", 0) * 100,
            "teamDmgPct": ch.get("teamDamagePercentage", 0) * 100,
            "dmgPerMin": ch.get("damagePerMinute", 0),
            "goldPerMin": ch.get("goldPerMinute", 0),
            "deaths": p.get("deaths", 0),
            "visionPerMin": ch.get("visionScorePerMinute", 0),
            "controlWards": ch.get("controlWardsPlaced", 0),
            "soloKills": ch.get("soloKills", 0),
            "kda": ch.get("kda", 0),
            "laneMinions10": ch.get("laneMinionsFirst10Minutes", 0),
        })
    keys = ["csPerMin", "kp", "teamDmgPct", "dmgPerMin", "goldPerMin", "deaths",
            "visionPerMin", "controlWards", "soloKills", "kda", "laneMinions10"]
    return {"n": len(rows), "means": {k: round(mean([r[k] for r in rows]), 2) for k in keys}}


def main():
    print("Building records...")
    recs = build_records(MDIR, TDIR, PUUID, solo_only=True)
    print(f"  {len(recs)} ranked-solo games")

    # overall summary
    n = len(recs)
    w = sum(r["win"] for r in recs)
    adc = [r for r in recs if r["position"] == "BOTTOM"]
    summary = {
        "player": "Topcheese044#NA1", "puuid": PUUID,
        "rank": "Diamond III (84 LP at pull)",
        "level": 346,
        "nGames": n, "wins": w, "losses": n - w, "wr": round(100 * w / n, 1),
        "dateFrom": dt.date.fromtimestamp(recs[0]["ts"]).isoformat(),
        "dateTo": dt.date.fromtimestamp(recs[-1]["ts"]).isoformat(),
        "adcGames": len(adc),
        "championsPlayed": len(set(r["champion"] for r in recs)),
    }

    # his overall means for the same keys as the Diamond benchmark (true head-to-head)
    bench = benchmark_block()
    if bench:
        bk = list(bench["means"].keys())
        bench["hisMeans"] = {k: round(mean(vals(recs, k)) or 0, 2) for k in bk}

    analysis = {
        "summary": summary,
        "benchmark": bench,
        "winLoss": win_loss_diff(recs),
        "champions": per_champion(recs),
        "matchups": matchups(recs),
        "time": time_patterns(recs),
        "form": recent_form(recs),
        "deaths": {
            "avgFirstDeathMin": round(mean(vals(recs, "firstDeathMin")) or 0, 2),
            "avgDeathsBefore15": round(mean(vals(recs, "deathsBefore15")) or 0, 2),
            "pctGamesEarlyDeath": round(100 * sum(1 for r in recs if (r.get("deathsBefore10") or 0) > 0) / n, 1),
        },
    }
    out_path = os.path.join(OUT, "analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    print(f"Wrote {out_path}")

    # console highlights
    print(f"\nOverall: {summary['wr']}% WR over {n} games ({summary['dateFrom']} -> {summary['dateTo']})")
    print(f"Inferred UTC offset: {analysis['time']['inferredUtcOffset']} "
          f"({analysis['time']['nSessions']} sessions, avg {analysis['time']['avgSessionLen']} games)")
    print("\nTop win-vs-loss differentiators (by effect size):")
    for r in analysis["winLoss"][:8]:
        print(f"  {r['label']:<32} win {r['winMean']:>8} | loss {r['lossMean']:>8} | d={r['cohensD']}")
    print("\nChampions (>=15 games):")
    for c in analysis["champions"]:
        if c["games"] >= 15:
            print(f"  {c['champion']:<14} {c['games']:>4}g  {c['wr']:>5}% WR  kda {c['kda']:>4}  "
                  f"kp {c['kp']:>4}  dmg% {c['teamDmgPct']:>4}")
    print("\nWR by streak state:")
    for b in analysis["time"]["byStreak"]:
        print(f"  {b['bucket']:<16} {b['wr']:>5}% ({b['games']}g)")
    print("\nWR by game-in-session:")
    for b in analysis["time"]["bySessionGame"]:
        print(f"  game {b['bucket']:<3} {b['wr']:>5}% ({b['games']}g)")
    print("\nWR by games-per-day:")
    for b in analysis["time"]["byGamesPerDay"]:
        print(f"  {b['bucket']:<6} {b['wr']:>5}% ({b['games']}g)")


if __name__ == "__main__":
    main()
