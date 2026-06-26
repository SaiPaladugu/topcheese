# topcheese — League of Legends account data

Data-analysis project on the account **`Topcheese044#NA1`** (NA region).

**🔗 Live dashboard:** https://topcheese044.vercel.app
**📄 Full written report:** [REPORT.md](REPORT.md)

- **PUUID:** `YjdM96oTQM4DnqbroX9G_BaMKfjc_IDyAhjq7MyDHyaEgxBXG2ehQOpQi_nAZcR4IhdRL6vTcHfyrA`

## Stage 1 — Data acquisition (this repo)

`fetch.py` pulls everything the Riot API exposes for the account and writes raw
JSON to `data/raw/`. It is **resumable**: already-downloaded match/timeline files
are skipped, so a re-run after a rate-limit interruption continues where it left off.

### Run it

```bash
# key lives in .env as RIOT_API_KEY=... (gitignored)
python fetch.py
```

Dev keys expire ~24h after issue; refresh the key in `.env` if you get 401/403.

### What gets pulled

| File | Endpoint | Contents |
|------|----------|----------|
| `data/raw/account.json` | Account-V1 | puuid, gameName, tagLine |
| `data/raw/summoner.json` | Summoner-V4 | level, encrypted ids, profile icon |
| `data/raw/league_entries.json` | League-V4 | ranked solo/flex tier, LP, W/L |
| `data/raw/champion_mastery.json` | Champion-Mastery-V4 | every champ: mastery level, points, last-played |
| `data/raw/mastery_score.json` | Champion-Mastery-V4 | total mastery score |
| `data/raw/active_game.json` | Spectator-V5 | live game if currently in one |
| `data/raw/match_ids.json` | Match-V5 | all available match ids (all queues) |
| `data/raw/matches/<id>.json` | Match-V5 | full per-match detail (every participant, stats, items, etc.) |
| `data/raw/timelines/<id>.json` | Match-V5 | frame-by-frame timeline (positions, events, gold curves) |

> Match-V5 history only reaches back to ~mid-2021 (when the endpoint launched);
> older games are not retrievable via the API.

## Files

- `riot_client.py` — HTTP client: rate limiting (20/s + 100/2min), 429/5xx retries, browser UA to clear Cloudflare.
- `fetch.py` — orchestrates the full pull.
- `.env` — `RIOT_API_KEY` (gitignored).

## Stage 1.5 — Diamond-ADC benchmarks

`benchmark_fetch.py` samples the Diamond solo-queue ladder and pulls a few hundred
real Diamond ADC games into `data/benchmark/`, so Stage 2 can compare Topcheese
against actual peers (computed baselines) — then sanity-checked against published
reference numbers (League of Graphs / U.GG / LeagueMath). Run it **after** `fetch.py`
finishes so the two don't contend for the shared rate limit:

```bash
python benchmark_fetch.py
```

## Stage 2 — Analysis (everything possible)

Built on the raw JSON in `data/raw/` + benchmarks in `data/benchmark/`, using
pandas/numpy/matplotlib + the Data Dragon maps in `data/static/`. Focus: actionable
levers to raise solo-queue win rate — lane diffs @10/@14, death timings, damage
share, kill participation, champion-pool win rates, vision, objective participation.

### Reusable tooling considered (we kept our own fetcher + pandas)

- [RiotWatcher](https://github.com/pseudonym117/Riot-Watcher) · [Cassiopeia](https://github.com/meraki-analytics/cassiopeia) · [Pulsefire](https://github.com/iann838/pulsefire) — mature API wrappers.
- The "actionable coaching" layer has no maintained drop-in (closest, [solo-queue](https://github.com/sachanganesh/solo-queue), is archived) — so we build the analysis ourselves.
