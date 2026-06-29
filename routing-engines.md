# Routing engines

Two engines, chosen automatically by `scripts/route.py`:

- **Single shaped route** → OpenRouteService (best avoid-busy-road control).
- **Several options requested** (`--alternatives N`, N>1) → BRouter (returns genuinely distinct lines).

Override with `--engine ors|brouter|auto`.

## OpenRouteService (default)

A personal ORS key is embedded in `route.py`, so this works with no setup. To rotate the key without editing the file, set an `ORS_API_KEY` environment variable, which takes precedence over the embedded one.

- Profiles: `cycling-regular`, `cycling-road`, `cycling-mountain`, `cycling-electric`, `foot-walking`, `foot-hiking`.
- Avoid busy roads with `--avoid ferries,steps,fords` on cycling/foot, or add `highways,tollways` on driving. The script filters the list to what each profile accepts, so passing `highways` on a bike profile is harmless (it is dropped). Cycling and foot profiles avoid trunk roads inherently, so you rarely need an explicit avoid for quietness.
- For finer control (steering around a specific motorway or bad junction) ORS supports `avoid_polygons`; if you need it, extend `_ors()` to pass a polygon under `options`.
- Coordinates are passed start, [vias], end. Add via-points to force the line through scenic/quiet areas.
- ORS does not produce the multi-option alternatives well for loops or via-routes, which is why the options flow uses BRouter.

## BRouter (no key; used for options and as fallback)

Purpose-built for pleasant cycling and hiking, and returns up to four genuinely different alternatives, which is ideal for the user's "give me options" requests.

- Profiles mapped from the activity: road cycling defaults to `trekking` (quiet, lane-biased), `fastbike` for a faster road line, `gravel`, `mtb`, and `hiking-beta` for foot.
- `--alternatives N` writes N variants as `<out>-1.gpx`, `<out>-2.gpx`, ... Use this to produce the fastest / most scenic / most fun options, then describe each from its distance and climb.
- BRouter already biases away from heavy traffic, so it pairs well with the scenic via-point shaping below.

## Shaping for scenic and quiet (applies to both engines)

The engine gives a sensible line between points. The *craft* is choosing the points, and the cardinal rule is: **do not anchor on town or place names.**

A geocoded settlement resolves to its centre, so using it as a via forces the route to dive into the town centre and back out, an ugly dog-leg. Instead:

1. Start with origin and destination only. Route it and look at the line.
2. If it already runs through pleasant, quiet country, stop. The bike/foot profiles do a lot of this for free.
3. To bias it onto a feature (coast road, ridge, canal towpath, NCN cycleway), add ONE via that is a coordinate sitting *on that road or path*, in the direction of travel, read off the map. Not the nearby town.
4. Re-run and check the routed distance against the target; nudge the on-route via until within ~5%.
5. **Inspect for spurs.** If the line darts somewhere and returns along the same road, the via is off the through-line: delete it or move it onto the through-road.
6. Prefer adding distance over a busy stretch, but never accept a pointless detour.

Geocode place names only for the genuine start, the destination, and explicitly requested stops, never to invent intermediate "go via this town" points.

## Common failure modes

- A via-point dropped on the wrong side of a river/motorway forces a long detour. Move it onto the correct lane/path.
- Foot routing on BRouter (`hiking-beta`) is weaker than ORS foot profiles; if a key is available, foot activities are better on ORS.
- Very long routes can time out; split into legs and concatenate the GPX track segments if needed.
