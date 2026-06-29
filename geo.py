#!/usr/bin/env python3
"""Geo helpers: geocode place names and compute great-circle distance.

CLI:
  python geo.py geocode "Victoria Park, London"
  python geo.py distance 50.80 -0.40 50.74 -0.30
"""
import sys
import json
import math
import time
import urllib.parse
import urllib.request

USER_AGENT = "alpn-route-planner/1.0 (personal route planning)"


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def path_length_km(coords):
    """coords: list of (lat, lon[, ele]). Returns total km along the path."""
    total = 0.0
    for i in range(1, len(coords)):
        total += haversine_km(coords[i - 1][0], coords[i - 1][1], coords[i][0], coords[i][1])
    return total


def geocode(query, country=None, limit=1):
    """Resolve a place name to coordinates via OpenStreetMap Nominatim.

    Returns a list of dicts: {name, lat, lon}.
    """
    params = {"q": query, "format": "jsonv2", "limit": str(limit)}
    if country:
        params["countrycodes"] = country
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    time.sleep(1)  # Nominatim courtesy: max 1 req/s
    out = []
    for item in data:
        out.append({
            "name": item.get("display_name", query),
            "lat": float(item["lat"]),
            "lon": float(item["lon"]),
        })
    return out


def _main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "geocode":
        q = argv[1]
        country = argv[2] if len(argv) > 2 else None
        res = geocode(q, country=country, limit=5)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    if cmd == "distance":
        lat1, lon1, lat2, lon2 = map(float, argv[1:5])
        print(round(haversine_km(lat1, lon1, lat2, lon2), 3))
        return 0
    print("Unknown command:", cmd)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
