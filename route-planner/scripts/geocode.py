#!/usr/bin/env python3
"""Turn street addresses into latitude/longitude using OpenStreetMap Nominatim.

Standard library only -- no pip install, no API key. Nominatim is free but rate
limited to ~1 request/second and requires a descriptive User-Agent, both of which
this script respects. For heavy/commercial use, swap in a paid geocoder.

Input: same shape as optimize_route.py expects, but stops only need an "address"
(or "name" used as the query). Output: the same stops enriched with lat/lon, ready
to pipe straight into optimize_route.py.

Examples:
  python3 geocode.py stops.json > stops.geocoded.json
  python3 geocode.py stops.csv --json-out | python3 optimize_route.py --format json
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "route-planner-skill/1.0 (https://github.com/ALPN-Digital/Route-Planner)"
RATE_LIMIT_SECONDS = 1.1


class GeocodeError(Exception):
    """Raised for user-facing geocoding problems."""


def geocode_one(query: str) -> tuple[float, float]:
    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": 1})
    req = urllib.request.Request(f"{NOMINATIM_URL}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not data:
        raise GeocodeError(f"No geocoding result for {query!r}")
    return float(data[0]["lat"]), float(data[0]["lon"])


def load_stops(raw: str, fmt: str) -> list[dict]:
    if fmt == "json":
        data = json.loads(raw)
        stops = data["stops"] if isinstance(data, dict) else data
        return [dict(s) for s in stops]
    reader = csv.DictReader(io.StringIO(raw))
    return [dict(row) for row in reader]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Geocode addresses to lat/lon via Nominatim.")
    parser.add_argument("input", nargs="?", help="Stops file (JSON or CSV). Omit to read stdin.")
    parser.add_argument("--format", choices=["json", "csv"], help="Override format detection.")
    parser.add_argument("--json-out", action="store_true", default=True,
                        help="Emit JSON (default).")
    args = parser.parse_args(argv)

    try:
        raw = open(args.input, encoding="utf-8").read() if args.input else sys.stdin.read()
        fmt = args.format or ("csv" if args.input and args.input.lower().endswith(".csv") else "json")
        stops = load_stops(raw, fmt)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    enriched: list[dict] = []
    for i, stop in enumerate(stops):
        out = dict(stop)
        if out.get("lat") in (None, "") or out.get("lon") in (None, ""):
            query = stop.get("address") or stop.get("name")
            if not query:
                print(f"Error: stop {i + 1} has no address or name to geocode.", file=sys.stderr)
                return 1
            try:
                if i:
                    time.sleep(RATE_LIMIT_SECONDS)
                lat, lon = geocode_one(query)
            except (GeocodeError, urllib.error.URLError) as exc:
                print(f"Error geocoding {query!r}: {exc}", file=sys.stderr)
                return 1
            out["lat"], out["lon"] = lat, lon
            print(f"  geocoded: {query} -> {lat}, {lon}", file=sys.stderr)
        else:
            out["lat"], out["lon"] = float(out["lat"]), float(out["lon"])
        if "name" not in out:
            out["name"] = out.get("address", f"Stop {i + 1}")
        enriched.append(out)

    print(json.dumps({"stops": enriched}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
