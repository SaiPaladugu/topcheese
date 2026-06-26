"""
Stage 1.5: Build our OWN Diamond-ADC benchmark dataset by sampling the ranked
ladder, so Stage 2 can compare Topcheese044 against real Diamond ADC baselines
(not just published reference numbers).

Method:
  1. Page the Diamond solo-queue ladder (League-V4) -> pool of player puuids.
  2. For each sampled player, pull recent RANKED_SOLO (queue 420) match ids.
  3. Download each unique match (+ timeline for @10/@14 lane diffs).
  4. Record every performance where the sampled player played BOTTOM (ADC) — these
     are bona-fide Diamond-MMR ADC games -> data/benchmark/adc_index.json.

Resumable: skips already-downloaded matches/timelines. Caps below bound the cost;
run it AFTER fetch.py finishes so the two don't fight over the shared rate limit.
"""
import os
import json

from riot_client import RiotClient

PLATFORM = "na1.api.riotgames.com"
REGIONAL = "americas.api.riotgames.com"
QUEUE_SOLO = 420

# --- cost caps (tweak freely) ---
DIVISIONS = ["I", "II", "III", "IV"]   # Diamond tiers (matches his III)
LADDER_PAGES_PER_DIV = 2               # ~205 entries/page
TARGET_PLAYERS = 120                   # sampled Diamond players
GAMES_PER_PLAYER = 8                   # recent ranked games pulled per player
TARGET_ADC_PERFS = 300                 # stop once we have this many Diamond ADC games

HERE = os.path.dirname(os.path.abspath(__file__))
BM = os.path.join(HERE, "data", "benchmark")
MDIR = os.path.join(BM, "matches")
TDIR = os.path.join(BM, "timelines")
for d in (BM, MDIR, TDIR):
    os.makedirs(d, exist_ok=True)


def save(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def main():
    c = RiotClient()

    # 1. Sample the Diamond ladder for player puuids
    print("[1] Sampling Diamond solo-queue ladder")
    players = {}  # puuid -> entry
    for div in DIVISIONS:
        for page in range(1, LADDER_PAGES_PER_DIV + 1):
            rows = c.get(PLATFORM, f"/lol/league/v4/entries/RANKED_SOLO_5x5/DIAMOND/{div}",
                         params={"page": page})
            if not rows:
                break
            for r in rows:
                pid = r.get("puuid")
                if pid:
                    players[pid] = {"division": div, "lp": r.get("leaguePoints"),
                                    "wins": r.get("wins"), "losses": r.get("losses")}
            print(f"  D{div} p{page}: +{len(rows)} (pool {len(players)})")
            if len(players) >= TARGET_PLAYERS * 4:
                break
        if len(players) >= TARGET_PLAYERS * 4:
            break
    sample = list(players.items())[:TARGET_PLAYERS]
    save(os.path.join(BM, "players.json"), {p: m for p, m in sample})
    print(f"  sampled {len(sample)} players")

    # 2-4. Collect matches and ADC performances
    print("[2] Collecting ranked matches + ADC performances")
    adc_index = []
    seen_matches = set()
    for i, (puuid, _) in enumerate(sample, 1):
        if len(adc_index) >= TARGET_ADC_PERFS:
            print(f"  reached target of {TARGET_ADC_PERFS} ADC performances")
            break
        ids = c.get(REGIONAL, f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
                    params={"queue": QUEUE_SOLO, "start": 0, "count": GAMES_PER_PLAYER})
        if not ids:
            continue
        for mid in ids:
            if mid in seen_matches:
                # still check if this puuid was ADC in an already-saved match
                pass
            seen_matches.add(mid)
            mpath = os.path.join(MDIR, f"{mid}.json")
            tpath = os.path.join(TDIR, f"{mid}.json")
            if os.path.exists(mpath):
                with open(mpath, encoding="utf-8") as f:
                    m = json.load(f)
            else:
                m = c.get(REGIONAL, f"/lol/match/v5/matches/{mid}")
                if not m:
                    continue
                save(mpath, m)
            if not os.path.exists(tpath):
                t = c.get(REGIONAL, f"/lol/match/v5/matches/{mid}/timeline")
                if t:
                    save(tpath, t)
            # is THIS sampled player the ADC here?
            for part in m.get("info", {}).get("participants", []):
                if part.get("puuid") == puuid and part.get("teamPosition") == "BOTTOM":
                    adc_index.append({"matchId": mid, "puuid": puuid,
                                      "championId": part.get("championId"),
                                      "win": part.get("win")})
                    break
        if i % 10 == 0:
            print(f"  player {i}/{len(sample)} | matches {len(seen_matches)} | "
                  f"ADC perfs {len(adc_index)} | api {c.request_count}")

    save(os.path.join(BM, "adc_index.json"), adc_index)
    print(f"\nDONE. Diamond ADC performances: {len(adc_index)} "
          f"across {len(seen_matches)} matches. API requests: {c.request_count}")


if __name__ == "__main__":
    main()
