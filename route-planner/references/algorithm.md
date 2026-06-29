# How the optimizer works

`optimize_route.py` solves a small **Traveling Salesman Problem (TSP)**: given a set
of stops, find the visiting order with the shortest total distance. TSP is NP-hard, so
the solver picks its strategy based on input size:

- **≤ 12 stops → exact.** [Held-Karp](https://en.wikipedia.org/wiki/Held%E2%80%93Karp_algorithm)
  dynamic programming returns the provably shortest tour in `O(2^n · n^2)` time. It
  honors a fixed start, an optional fixed end, and round trips.
- **> 12 stops → heuristic.** Held-Karp's memory grows with `2^n`, so larger inputs use
  the fast multi-start local search below, which gets within a few percent of optimal.

(The 12-stop cutoff is `EXACT_MAX_STOPS` in the script — raise it if you want exactness
for slightly larger inputs and don't mind the extra time/memory.)

## Heuristic pipeline (large inputs)

1. **Distance matrix** — pairwise [haversine](https://en.wikipedia.org/wiki/Haversine_formula)
   (great-circle) distances between every stop, in kilometers.

2. **Nearest-neighbor construction** — start at the chosen stop and repeatedly hop to
   the closest unvisited stop. Fast, but typically 15–25% above optimal on its own.

3. **Local search** — alternate two move types until neither improves the tour:
   - **2-opt**: reverse a segment of the route when doing so removes a crossing /
     shortens the path. Great at untangling.
   - **Or-opt**: relocate a short chain (1–3 stops) to a cheaper position. Catches
     improvements 2-opt can't express.

4. **Multi-start** — repeat steps 2–3 from several deterministic starting orders and
   keep the best result. This escapes local optima. The number of restarts scales
   down as the input grows (more restarts are cheap when there are few stops).

Determinism: the shuffles use a small seeded PRNG, so the same input always yields the
same route (important for reproducible tests and diffs).

## Constraints supported

- **Fixed start** (`--start`) — pin the first stop (depot, home, current location).
- **Fixed end** (`--end`) — pin the last stop.
- **Round trip** (`--round-trip`) — close the loop back to the start; the cost model
  and both move operators account for the return leg.

## Quality

For ≤12 stops the result is exact (Held-Karp), verified against brute force in the test
suite. Beyond that, the heuristic's gap to optimal is typically a couple percent;
~50 stops solve in about a second and ~100 in a few seconds.

## Tuning / extending

- **Exactness for larger inputs**: raise `EXACT_MAX_STOPS` (watch memory — it's `2^n`).
- **More accuracy on big inputs**: raise the `restarts` cap in `optimize()`.
- **Road distance instead of straight-line**: replace `haversine_km` /
  `build_distance_matrix` with a call to a routing API's distance-matrix endpoint,
  then feed the resulting matrix into the same local search unchanged.
- **Time windows / capacities (VRP)**: this is a pure TSP. For vehicle-routing
  constraints, consider [Google OR-Tools](https://developers.google.com/optimization/routing).
