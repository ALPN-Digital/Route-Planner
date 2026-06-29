#!/usr/bin/env python3
"""Optimize the visiting order of a set of stops (a small Traveling Salesman solve).

Standard library only -- no pip install required. Works fully offline as long as
every stop already has coordinates. Use geocode.py first if you only have addresses.

Input formats (auto-detected):
  - JSON: a list of stops, or {"stops": [...]}. Each stop is either
        {"name": "...", "lat": 40.0, "lon": -73.0}
    or  {"name": "...", "address": "..."}  (requires coordinates -- run geocode.py first)
  - CSV: a header row with columns name,lat,lon  (address column also accepted)

Examples:
  python3 optimize_route.py stops.json
  python3 optimize_route.py stops.csv --start "Warehouse" --round-trip
  cat stops.json | python3 optimize_route.py --format json --json-out

Algorithm: nearest-neighbor construction followed by 2-opt improvement, using
great-circle (haversine) distance. Exact for tiny inputs in practice and very
good for up to a few hundred stops.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
import sys
from typing import Optional

EARTH_RADIUS_KM = 6371.0088


class RouteError(Exception):
    """Raised for user-facing input problems (bad data, missing coords, etc.)."""


def haversine_km(a: dict, b: dict) -> float:
    """Great-circle distance between two {lat, lon} points, in kilometers."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def build_distance_matrix(stops: list[dict]) -> list[list[float]]:
    n = len(stops)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(stops[i], stops[j])
            matrix[i][j] = matrix[j][i] = d
    return matrix


def route_length(order: list[int], dist: list[list[float]], round_trip: bool) -> float:
    total = sum(dist[order[i]][order[i + 1]] for i in range(len(order) - 1))
    if round_trip and len(order) > 1:
        total += dist[order[-1]][order[0]]
    return total


def nearest_neighbor(dist: list[list[float]], start: int) -> list[int]:
    n = len(dist)
    unvisited = set(range(n))
    unvisited.remove(start)
    order = [start]
    current = start
    while unvisited:
        nxt = min(unvisited, key=lambda j: dist[current][j])
        order.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return order


def two_opt(order: list[int], dist: list[list[float]], round_trip: bool,
            fixed_start: bool, fixed_end: bool) -> list[int]:
    """Iteratively reverse segments while it shortens the route.

    fixed_start/fixed_end keep the first/last stop pinned (e.g. depart from the
    warehouse, finish at home). The endpoints excluded from swapping respect that.
    """
    order = order[:]
    n = len(order)
    if n < 4:
        return order
    lo = 1 if fixed_start else 0
    improved = True
    while improved:
        improved = False
        for i in range(lo, n - 1):
            # When the end is pinned (or it's a round trip back to start), the
            # final node must stay put, so the inner loop stops one short.
            hi = n - 1 if (fixed_end or round_trip) else n
            for k in range(i + 1, hi):
                a, b = order[i - 1], order[i]
                c = order[k]
                # The node that follows the reversed segment: the next stop, the
                # wrap-around start for a round trip, or nothing at the path's end.
                if k + 1 < n:
                    d = order[k + 1]
                elif round_trip:
                    d = order[0]
                else:
                    d = None
                if d is None:
                    # Reversing the tail of an open path only swaps edge (a, b).
                    before = dist[a][b]
                    after = dist[a][c]
                else:
                    before = dist[a][b] + dist[c][d]
                    after = dist[a][c] + dist[b][d]
                if after + 1e-12 < before:
                    order[i:k + 1] = reversed(order[i:k + 1])
                    improved = True
    return order


def or_opt(order: list[int], dist: list[list[float]], round_trip: bool,
           fixed_start: bool, fixed_end: bool) -> list[int]:
    """Relocate short chains (length 1-3) to a cheaper position.

    Complements 2-opt: 2-opt reverses segments, Or-opt moves them. Together they
    escape local optima that either move alone gets stuck in.
    """
    order = order[:]
    n = len(order)
    lo = 1 if fixed_start else 0
    hi = n - 1 if fixed_end else n
    improved = True
    while improved:
        improved = False
        for seg_len in (1, 2, 3):
            for i in range(lo, hi - seg_len + 1):
                seg = order[i:i + seg_len]
                rest = order[:i] + order[i + seg_len:]
                base = route_length(order, dist, round_trip)
                # Never insert past a pinned end stop (keep it last).
                last_pos = len(rest) - 1 if fixed_end else len(rest)
                for j in range(lo, last_pos + 1):
                    candidate = rest[:j] + seg + rest[j:]
                    if candidate == order:
                        continue
                    if route_length(candidate, dist, round_trip) + 1e-12 < base:
                        order = candidate
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break
    return order


def local_search(order: list[int], dist: list[list[float]], round_trip: bool,
                 fixed_start: bool, fixed_end: bool) -> list[int]:
    """Alternate 2-opt and Or-opt until neither improves the tour."""
    prev = None
    while order != prev:
        prev = order
        order = two_opt(order, dist, round_trip, fixed_start, fixed_end)
        order = or_opt(order, dist, round_trip, fixed_start, fixed_end)
    return order


def _seeded_shuffle(items: list[int], seed: int) -> list[int]:
    """Deterministic Fisher-Yates shuffle (no global RNG -> reproducible runs)."""
    items = items[:]
    state = (seed * 2654435761 + 1) & 0xFFFFFFFF
    for i in range(len(items) - 1, 0, -1):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        j = state % (i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def held_karp(dist: list[list[float]], start: int, round_trip: bool,
              end_index: Optional[int]) -> list[int]:
    """Exact optimal tour via Held-Karp dynamic programming.

    O(2^n * n^2) time, so only used for small inputs. Honors a fixed start, an
    optional fixed end (open path), and round trips. Round trip ignores end_index.
    """
    nodes = [i for i in range(len(dist)) if i != start]
    m = len(nodes)
    if m == 0:
        return [start]
    INF = float("inf")
    size = 1 << m
    dp = [[INF] * m for _ in range(size)]
    parent = [[-1] * m for _ in range(size)]
    for i, node in enumerate(nodes):
        dp[1 << i][i] = dist[start][node]
    for mask in range(size):
        for last in range(m):
            cost = dp[mask][last]
            if cost == INF or not (mask >> last) & 1:
                continue
            for nxt in range(m):
                if (mask >> nxt) & 1:
                    continue
                nm = mask | (1 << nxt)
                c = cost + dist[nodes[last]][nodes[nxt]]
                if c < dp[nm][nxt]:
                    dp[nm][nxt] = c
                    parent[nm][nxt] = last
    full = size - 1
    best, best_last = INF, -1
    for last in range(m):
        if end_index is not None and not round_trip and nodes[last] != end_index:
            continue
        total = dp[full][last] + (dist[nodes[last]][start] if round_trip else 0.0)
        if total < best:
            best, best_last = total, last
    order: list[int] = []
    mask, last = full, best_last
    while last != -1:
        order.append(nodes[last])
        last, mask = parent[mask][last], mask ^ (1 << last)
    order.reverse()
    return [start] + order


# Above this many stops, exact Held-Karp becomes too expensive; fall back to the
# multi-start heuristic.
EXACT_MAX_STOPS = 12


def optimize(stops: list[dict], start_index: int = 0, round_trip: bool = False,
             end_index: Optional[int] = None) -> dict:
    if not stops:
        raise RouteError("No stops provided.")
    for s in stops:
        if "lat" not in s or "lon" not in s:
            raise RouteError(
                f"Stop {s.get('name', s)!r} has no coordinates. "
                "Run geocode.py on the addresses first."
            )
    if len(stops) == 1:
        order = [0]
    elif len(stops) <= EXACT_MAX_STOPS:
        # Small enough to solve exactly.
        dist = build_distance_matrix(stops)
        order = held_karp(dist, start_index, round_trip, end_index)
    else:
        dist = build_distance_matrix(stops)
        fixed_end = end_index is not None
        n = len(stops)
        middle = [i for i in range(n) if i != start_index and i != end_index]

        def assemble(mid: list[int]) -> list[int]:
            tour = [start_index] + mid
            if fixed_end:
                tour.append(end_index)
            return tour

        # Multi-start: nearest-neighbor plus a handful of deterministic shuffles,
        # each refined by local search. More starts for smaller inputs (cheap).
        nn = nearest_neighbor(dist, start_index)
        if fixed_end:
            nn.remove(end_index)
            nn.append(end_index)
        candidates = [nn]
        restarts = min(40, max(8, 200 // n))
        for seed in range(restarts):
            candidates.append(assemble(_seeded_shuffle(middle, seed + 1)))

        best_order, best_len = None, float("inf")
        for cand in candidates:
            refined = local_search(cand, dist, round_trip, fixed_start=True, fixed_end=fixed_end)
            length = route_length(refined, dist, round_trip)
            if length < best_len:
                best_order, best_len = refined, length
        order = best_order

    dist = build_distance_matrix(stops) if len(stops) > 1 else [[0.0]]
    ordered_stops = [stops[i] for i in order]
    total_km = route_length(order, dist, round_trip)
    legs = []
    for i in range(len(order) - 1):
        legs.append({
            "from": stops[order[i]]["name"],
            "to": stops[order[i + 1]]["name"],
            "km": round(dist[order[i]][order[i + 1]], 3),
        })
    if round_trip and len(order) > 1:
        legs.append({
            "from": stops[order[-1]]["name"],
            "to": stops[order[0]]["name"],
            "km": round(dist[order[-1]][order[0]], 3),
        })
    return {
        "order": [s["name"] for s in ordered_stops],
        "stops": ordered_stops,
        "legs": legs,
        "total_km": round(total_km, 3),
        "total_miles": round(total_km * 0.621371, 3),
        "round_trip": round_trip,
        "google_maps_url": google_maps_url(ordered_stops, round_trip),
    }


def google_maps_url(ordered_stops: list[dict], round_trip: bool) -> str:
    """A shareable Google Maps directions link for the optimized order."""
    points = [f"{s['lat']},{s['lon']}" for s in ordered_stops]
    if round_trip and len(points) > 1:
        points.append(points[0])
    return "https://www.google.com/maps/dir/" + "/".join(points)


def _find_index(stops: list[dict], name: Optional[str], default: Optional[int]) -> Optional[int]:
    if name is None:
        return default
    for i, s in enumerate(stops):
        if s.get("name", "").strip().lower() == name.strip().lower():
            return i
    raise RouteError(f"Stop named {name!r} not found.")


def parse_stops(raw: str, fmt: str) -> list[dict]:
    if fmt == "json":
        data = json.loads(raw)
        stops = data["stops"] if isinstance(data, dict) else data
    elif fmt == "csv":
        reader = csv.DictReader(io.StringIO(raw))
        stops = [dict(row) for row in reader]
    else:
        raise RouteError(f"Unknown format: {fmt}")

    cleaned: list[dict] = []
    for i, s in enumerate(stops):
        stop = {"name": (s.get("name") or s.get("address") or f"Stop {i + 1}").strip()}
        if s.get("address"):
            stop["address"] = s["address"]
        for key in ("lat", "lon"):
            if s.get(key) not in (None, ""):
                stop[key] = float(s[key])
        cleaned.append(stop)
    return cleaned


def detect_format(path: Optional[str], explicit: Optional[str]) -> str:
    if explicit:
        return explicit
    if path and path.lower().endswith(".csv"):
        return "csv"
    return "json"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Optimize the order of route stops.")
    parser.add_argument("input", nargs="?", help="Path to stops file (JSON or CSV). Omit to read stdin.")
    parser.add_argument("--format", choices=["json", "csv"], help="Override input format detection.")
    parser.add_argument("--start", help="Name of the stop to start from (default: first stop).")
    parser.add_argument("--end", help="Name of the stop to finish at (pins the last stop).")
    parser.add_argument("--round-trip", action="store_true", help="Return to the start stop.")
    parser.add_argument("--json-out", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    try:
        if args.input:
            with open(args.input, "r", encoding="utf-8") as fh:
                raw = fh.read()
        else:
            raw = sys.stdin.read()
        fmt = detect_format(args.input, args.format)
        stops = parse_stops(raw, fmt)
        start_index = _find_index(stops, args.start, 0)
        end_index = _find_index(stops, args.end, None)
        result = optimize(stops, start_index=start_index, round_trip=args.round_trip,
                          end_index=end_index)
    except (RouteError, ValueError, KeyError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json_out:
        print(json.dumps(result, indent=2))
    else:
        print(format_human(result))
    return 0


def format_human(result: dict) -> str:
    lines = ["Optimized route:"]
    for i, name in enumerate(result["order"], 1):
        lines.append(f"  {i}. {name}")
    if result["round_trip"]:
        lines.append(f"  {len(result['order']) + 1}. {result['order'][0]} (return)")
    lines.append("")
    lines.append(f"Total distance: {result['total_km']} km ({result['total_miles']} mi)")
    lines.append(f"Google Maps:    {result['google_maps_url']}")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
