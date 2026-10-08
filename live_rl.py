"""Fetches the big live feed and keeps only the RL trips from rl_trips.json.
Writes rl_live.json (a few KB) with the live departure time at the origin stop of each trip:
{"updated": <epoch>, "trips": [{"id": static_trip_id, "d": "2026-10-09", "dep": <epoch>}]}
"""
import json, sys, urllib.request, time
from datetime import datetime

URL = "https://mkuran.pl/gtfs/polish_trains/updates.json"
src = sys.argv[1] if len(sys.argv) > 1 else None
raw = open(src, "rb").read() if src else urllib.request.urlopen(
    urllib.request.Request(URL, headers={"User-Agent": "transitwatch-rl"}), timeout=120).read()
feed = json.loads(raw)
known = json.load(open("rl_trips.json", encoding="utf-8"))
by_number = {v["n"]: k for k, v in known.items()}

def epoch(s):
    return int(datetime.fromisoformat(s).timestamp())

out = []
for u in feed["trip_updates"]:
    if u.get("agency_id") != "KM":
        continue
    tid = u["trip_id"]
    if tid not in known:
        # backup match (trip ids are not fully stable): train number, e.g. ["97110","1"] -> "97110/1"
        tid = by_number.get("/".join(u.get("numbers", [])))
        if tid is None:
            continue
    seq = known[tid]["seq"]
    for s in u["stop_times"]:
        if s["stop_sequence"] == seq:
            t = s.get("departure") or s.get("arrival")
            if t:
                out.append({"id": tid, "d": u["start_date"], "dep": epoch(t)})
            break

json.dump({"updated": int(time.time()), "trips": out}, open("rl_live.json", "w"), separators=(",", ":"))
print("rl_live.json:", len(out), "trips")
