---
name: route-planner
description: Plans and optimizes the order of multi-stop routes (deliveries, sales calls, errands, road trips). Use when the user gives a set of places, addresses, or coordinates and wants the shortest/fastest visiting order, a delivery sequence, a round trip, or a shareable Google Maps link. Handles geocoding addresses, fixing a start/end stop, and round trips.
license: MIT
---

# Route Planner

Turn a list of stops into an optimized visiting order and a shareable map link.

## When to use this skill

Trigger this skill whenever the user wants to order or sequence multiple places, e.g.:

- "What's the most efficient order to visit these 8 addresses?"
- "Plan my delivery route starting from the warehouse."
- "I have these stops, give me a round trip from home."
- "Optimize this sales-call list and give me a Google Maps link."

If there is only one stop, or the user just wants directions between two points, this
skill is unnecessary — answer directly or hand them a maps link.

## How it works

Two standard-library Python scripts (no `pip install`, no API key needed):

1. `scripts/geocode.py` — converts street addresses to latitude/longitude using the
   free OpenStreetMap Nominatim service. **Only needed if stops lack coordinates.**
2. `scripts/optimize_route.py` — computes the optimal visiting order. For ≤12 stops
   it solves exactly (Held-Karp); beyond that it uses a near-optimal heuristic
   (nearest-neighbor + 2-opt + Or-opt). Works over great-circle distance and emits an
   ordered list, per-leg distances, totals, and a Google Maps link.

## Workflow

1. **Collect the stops** from the user. Build a JSON file in this shape:
   ```json
   { "stops": [
       { "name": "Warehouse", "lat": 40.7128, "lon": -74.0060 },
       { "name": "Client A",  "address": "11 Wall St, New York, NY" }
   ] }
   ```
   `name` is optional (falls back to the address). Provide `lat`/`lon` when known;
   otherwise an `address` to geocode. CSV with `name,lat,lon` or `name,address`
   columns also works.

2. **Geocode if any stop is missing coordinates:**
   ```bash
   python3 scripts/geocode.py stops.json > stops.geocoded.json
   ```
   Skip this step entirely when every stop already has `lat`/`lon`.
   Nominatim is rate-limited to ~1 request/second, so this takes ~1s per address.

3. **Optimize the order:**
   ```bash
   python3 scripts/optimize_route.py stops.geocoded.json
   ```
   Useful flags:
   - `--start "Warehouse"` — pin the first stop (e.g. depot/home).
   - `--end "Home"` — pin the last stop.
   - `--round-trip` — return to the start at the end.
   - `--json-out` — machine-readable JSON instead of the human summary.
   - reads from stdin if no file is given (pair with `--format json|csv`).

4. **Report back to the user**: the ordered stop list, the total distance
   (km and miles), and the `google_maps_url` so they can open turn-by-turn
   directions. Mention if any address failed to geocode.

## One-liner (addresses → optimized route)

```bash
python3 scripts/geocode.py stops.csv --format csv \
  | python3 scripts/optimize_route.py --format json --start "Office" --round-trip
```

## Notes & limits

- Distances are straight-line (great-circle), not road distances. Order is reliable;
  the reported kilometers are an estimate. For exact drive times, plug the optimized
  order into a routing API (Google, Mapbox, OpenRouteService).
- Routing is exact for ≤12 stops and a near-optimal heuristic beyond that (~100 stops
  in a few seconds, within a few percent of optimal).
- Everything runs offline except geocoding. If the user already has coordinates,
  no network is used at all.
- See `references/algorithm.md` for how the optimizer works and how to tune it.
