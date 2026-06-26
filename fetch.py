"""
Stage 1: Pull EVERYTHING the Riot API exposes for Topcheese044#NA1 and save to disk.

Resumable: already-downloaded match files are skipped, so you can re-run after
a rate-limit interruption without losing progress.

Layout:
  data/raw/account.json                  Account-V1 (puuid, gameName, tagLine)
  data/raw/active_shard.json             Account-V1 active shard (lol)
  data/raw/summoner.json                 Summoner-V4 (level, ids, icon)
  data/raw/league_entries.json           League-V4 ranked (solo/flex tiers)
  data/raw/champion_mastery.json         Champion-Mastery-V4 (all champs)
  data/raw/mastery_score.json            Champion-Mastery-V4 total score
  data/raw/active_game.json              Spectator-V5 live game (if in one)
  data/raw/match_ids.json                All match ids (paginated, all queues)
  data/raw/matches/<MATCHID>.json        Match-V5 full match detail
  data/raw/timelines/<MATCHID>.json      Match-V5 frame-by-frame timeline
"""
import os
import json
import time

from riot_client import RiotClient

GAME_NAME = "topcheese044"
TAG_LINE = "NA1"
REGIONAL = "americas.api.riotgames.com"   # account-v1, match-v5
PLATFORM = "na1.api.riotgames.com"        # summoner, league, mastery, spectator

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")
MATCH_DIR = os.path.join(RAW, "matches")
TL_DIR = os.path.join(RAW, "timelines")
for d in (RAW, MATCH_DIR, TL_DIR):
    os.makedirs(d, exist_ok=True)


def save(name, obj):
    path = os.path.join(RAW, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(f"  saved {name}")


def main():
    c = RiotClient()

    # 1. Account-V1 -> puuid
    print("[1] Account-V1")
    account = c.get(REGIONAL, f"/riot/account/v1/accounts/by-riot-id/{GAME_NAME}/{TAG_LINE}")
    if not account:
        raise SystemExit("Account not found.")
    puuid = account["puuid"]
    save("account.json", account)
    print(f"  puuid = {puuid}")

    # (Account-V1 active-shards only supports val/lor/2xko, not lol — LoL uses
    #  fixed platform routing, so there's nothing to fetch here.)

    # 2. Summoner-V4
    print("[2] Summoner-V4")
    summoner = c.get(PLATFORM, f"/lol/summoner/v4/summoners/by-puuid/{puuid}")
    if summoner:
        save("summoner.json", summoner)

    # 3. League-V4 ranked entries (by-puuid is the current supported route)
    print("[3] League-V4 entries")
    entries = c.get(PLATFORM, f"/lol/league/v4/entries/by-puuid/{puuid}")
    if entries is None and summoner and summoner.get("id"):
        entries = c.get(PLATFORM, f"/lol/league/v4/entries/by-summoner/{summoner['id']}")
    save("league_entries.json", entries or [])

    # 4. Champion Mastery-V4
    print("[4] Champion-Mastery-V4")
    mastery = c.get(PLATFORM, f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}")
    save("champion_mastery.json", mastery or [])
    score = c.get(PLATFORM, f"/lol/champion-mastery/v4/scores/by-puuid/{puuid}")
    save("mastery_score.json", {"totalMasteryScore": score})

    # 5. Spectator-V5 active game (404 if not currently in a game)
    print("[5] Spectator-V5 active game")
    active = c.get(PLATFORM, f"/lol/spectator/v5/active-games/by-summoner/{puuid}")
    save("active_game.json", active or {"inGame": False})

    # 6. Match-V5 — paginate ALL match ids
    print("[6] Match-V5 ids (paginating all queues)")
    all_ids = []
    start = 0
    page = 100
    while True:
        ids = c.get(REGIONAL, f"/lol/match/v5/matches/by-puuid/{puuid}/ids",
                    params={"start": start, "count": page})
        if not ids:
            break
        all_ids.extend(ids)
        print(f"  +{len(ids)} ids (total {len(all_ids)})")
        if len(ids) < page:
            break
        start += page
    # de-dup, preserve order
    seen = set()
    all_ids = [m for m in all_ids if not (m in seen or seen.add(m))]
    save("match_ids.json", all_ids)
    print(f"  total matches available: {len(all_ids)}")

    # 7. Match details + timelines (resumable)
    print("[7] Match details + timelines")
    total = len(all_ids)
    for i, mid in enumerate(all_ids, 1):
        mpath = os.path.join(MATCH_DIR, f"{mid}.json")
        tpath = os.path.join(TL_DIR, f"{mid}.json")
        need_m = not os.path.exists(mpath)
        need_t = not os.path.exists(tpath)
        if not need_m and not need_t:
            continue
        if need_m:
            m = c.get(REGIONAL, f"/lol/match/v5/matches/{mid}")
            if m:
                with open(mpath, "w", encoding="utf-8") as f:
                    json.dump(m, f, indent=2)
        if need_t:
            t = c.get(REGIONAL, f"/lol/match/v5/matches/{mid}/timeline")
            if t:
                with open(tpath, "w", encoding="utf-8") as f:
                    json.dump(t, f, indent=2)
        if i % 10 == 0 or i == total:
            print(f"  {i}/{total} matches done (api requests so far: {c.request_count})")

    print(f"\nDONE. Total API requests: {c.request_count}")
    print(f"Matches saved: {len(os.listdir(MATCH_DIR))}, timelines: {len(os.listdir(TL_DIR))}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Elapsed: {time.time()-t0:.0f}s")
