"""
Fetch static reference data (Data Dragon + Riot static) so Stage 2 can map the
numeric ids in match data to human-readable names: champions, items, summoner
spells, runes, and queue types. Saved under data/static/.
"""
import os
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "data", "static")
os.makedirs(STATIC, exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 topcheese-analysis/1.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def save(name, obj):
    with open(os.path.join(STATIC, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    print(f"  saved static/{name}")


def main():
    versions = fetch("https://ddragon.leagueoflegends.com/api/versions.json")
    ver = versions[0]
    print(f"Latest Data Dragon version: {ver}")
    save("version.json", {"version": ver})

    base = f"https://ddragon.leagueoflegends.com/cdn/{ver}/data/en_US"
    for name, url in [
        ("champion.json", f"{base}/champion.json"),
        ("item.json", f"{base}/item.json"),
        ("summoner.json", f"{base}/summoner.json"),
        ("runesReforged.json", f"{base}/runesReforged.json"),
    ]:
        save(name, fetch(url))

    # Queue id -> description (static-data, community-maintained mirror by Riot)
    save("queues.json", fetch("https://static.developer.riotgames.com/docs/lol/queues.json"))
    # Map ids, game modes, game types
    save("maps.json", fetch("https://static.developer.riotgames.com/docs/lol/maps.json"))
    save("gameModes.json", fetch("https://static.developer.riotgames.com/docs/lol/gameModes.json"))
    save("gameTypes.json", fetch("https://static.developer.riotgames.com/docs/lol/gameTypes.json"))

    # Build a flat championId -> name lookup for convenience
    champ = fetch(f"{base}/champion.json")
    id_to_name = {int(c["key"]): c["id"] for c in champ["data"].values()}
    save("champion_id_to_name.json", id_to_name)
    print(f"  built championId map ({len(id_to_name)} champions)")


if __name__ == "__main__":
    main()
