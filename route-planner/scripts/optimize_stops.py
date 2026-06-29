#!/usr/bin/env python3
"""Order multiple stops into the shortest visiting sequence (a small TSP solve).

When the user wants to visit several places and doesn't care about the order
("plan a ride taking in these 6 cafes", "errand loop hitting all these shops"),
this finds the best order to visit them, then hands the ordered coordinates
straight to route.py / water_route.py to build the actual scenic line.

It optimizes *visiting order only* by great-circle distance. It does NOT route
the roads between stops — feed its output into the routing engine for that.

Exact (Held-Karp) for <=12 stops; nearest-neighbor + 2-opt heuristic beyond.
Standard library only (reuses geo.haversine_km).

CLI:
  python optimize_stops.py --stops "51.50,-0.12,Cafe A; 51.46,-0.17,Bakery; 51.52,-0.10,Deli"
  python optimize_stops.py --stops "..." --start "Cafe A" --round-trip
  python optimize_stops.py --stops "..." --start "Home" --end "Office"

Output (JSON):
  order        ordered stop names
  total_km     straight-line length of the visiting order
  points       "lat,lon; lat,lon; ..." ready for route.py --points
  named_stops  "lat,lon,Name; ..." ready for route.py --stops
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geo import haversine_km  # noqa: E402

EXACT_MAX_STOPS = 12


def parse_stops(s):
    """'lat,lon[,Name]; ...' -> list of {lat, lon, name}."""
    stops = []
    for i, chunk in enumerate(s.split(";")):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split(",")]
        if len(parts) < 2:
            raise ValueError(f"Stop {chunk!r} needs at least lat,lon.")
        name = ",".join(parts[2:]) if len(parts) > 2 else f"Stop {i + 1}"
        stops.append({"lat": float(parts[0]), "lon": float(parts[1]), "name": name})
    if len(stops) < 2:
        raise ValueError("Need at least two stops to order.")
    return stops


def build_matrix(stops):
    n = len(stops)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_km(stops[i]["lat"], stops[i]["lon"], stops[j]["lat"], stops[j]["lon"])
            m[i][j] = m[j][i] = d
    return m


def route_length(order, dist, round_trip):
    total = sum(dist[order[i]][order[i + 1]] for i in range(len(order) - 1))
    if round_trip and len(order) > 1:
        total += dist[order[-1]][order[0]]
    return total


def _nearest_neighbor(dist, start):
    n = len(dist)
    unvisited = set(range(n)) - {start}
    order = [start]
    while unvisited:
        nxt = min(unvisited, key=lambda j: dist[order[-1]][j])
        order.append(nxt)
        unvisited.discard(nxt)
    return order


def _two_opt(order, dist, round_trip, fixed_end):
    n = len(order)
    if n < 4:
        return order
    order = order[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, n - 1):
            hi = n - 1 if (fixed_end or round_trip) else n
            for k in range(i + 1, hi):
                a, b, c = order[i - 1], order[i], order[k]
                if k + 1 < n:
                    d = order[k + 1]
                elif round_trip:
                    d = order[0]
                else:
                    d = None
                if d is None:
                    before, after = dist[a][b], dist[a][c]
                else:
                    before, after = dist[a][b] + dist[c][d], dist[a][c] + dist[b][d]
                if after + 1e-12 < before:
                    order[i:k + 1] = reversed(order[i:k + 1])
                    improved = True
    return order


def _held_karp(dist, start, round_trip, end_index):
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
    order, mask, last = [], full, best_last
    while last != -1:
        order.append(nodes[last])
        last, mask = parent[mask][last], mask ^ (1 << last)
    order.reverse()
    return [start] + order


def optimize(stops, start_index=0, round_trip=False, end_index=None):
    n = len(stops)
    dist = build_matrix(stops)
    if n <= EXACT_MAX_STOPS:
        order = _held_karp(dist, start_index, round_trip, end_index)
    else:
        order = _nearest_neighbor(dist, start_index)
        if end_index is not None:
            order.remove(end_index)
            order.append(end_index)
        order = _two_opt(order, dist, round_trip, fixed_end=end_index is not None)
    ordered = [stops[i] for i in order]
    return {
        "order": [s["name"] for s in ordered],
        "total_km": round(route_length(order, dist, round_trip), 3),
        "round_trip": round_trip,
        "points": "; ".join(f"{s['lat']},{s['lon']}" for s in ordered)
                  + (f"; {ordered[0]['lat']},{ordered[0]['lon']}" if round_trip else ""),
        "named_stops": "; ".join(f"{s['lat']},{s['lon']},{s['name']}" for s in ordered),
    }


def _find_index(stops, name, default):
    if name is None:
        return default
    for i, s in enumerate(stops):
        if s["name"].strip().lower() == name.strip().lower():
            return i
    raise ValueError(f"Stop named {name!r} not found.")


def _main(argv=None):
    ap = argparse.ArgumentParser(description="Order multiple stops into the shortest visiting sequence.")
    ap.add_argument("--stops", required=True, help='"lat,lon[,Name]; ..." (two or more stops)')
    ap.add_argument("--start", help="name of the stop to start from (default: first)")
    ap.add_argument("--end", help="name of the stop to finish at")
    ap.add_argument("--round-trip", action="store_true", help="return to the start")
    a = ap.parse_args(argv)
    try:
        stops = parse_stops(a.stops)
        start_index = _find_index(stops, a.start, 0)
        end_index = _find_index(stops, a.end, None)
        result = optimize(stops, start_index=start_index, round_trip=a.round_trip,
                          end_index=end_index)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
