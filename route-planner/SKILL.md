---
name: route-planner
description: Expert multi-activity route planner that designs scenic, quiet routes for cycling, running, hiking, walking, and water sports (paddleboarding, kayaking, swimming, freediving) anywhere in the world and outputs a ready-to-ride GPX file. Use this skill whenever the user asks to plan, design, or map a ride, run, hike, walk, paddle, swim, or any outdoor route, even vaguely ("plan me a 100km ride", "find a scenic loop near me", "route to the best tacos on the west coast", "paddle to the wind farm and back"). Also trigger when the user gives a distance, a destination, an activity, or a vibe and wants route options, a GPX, time estimates, or weather for the day. Pulls the user's Strava history for pace, prefers quiet country roads and scenic terrain over busy roads and bike paths beside motorways, and always checks the weather for the planned day.
---

# Route Planner

Design the most scenic, lowest-traffic route for any activity, anywhere, and hand back a GPX the user can load straight onto their device, with an honest time estimate based on *their* fitness and a weather read for the day they are going.

## Golden rules

1. **Scenic and quiet beats fast and direct.** Default to country lanes, coast, woodland, river paths and parkland. Actively avoid A-roads, dual carriageways, and the classic trap of a cycle path that runs right beside a motorway. The user would rather add 5km than ride beside lorries.
2. **Estimates must be the user's, not generic.** Pull their Strava history for the activity and use their real moving speed. A 100km ride for them is not a 100km ride for a textbook.
3. **Never skip the weather.** Always fetch the forecast for the planned location and day before finalising. For water sports, wind and waves are go/no-go, not a footnote.
4. **Vague input is normal.** If the user is loose ("somewhere nice", "about two hours") or slightly wrong ("the wind farm off Brighton" when it is off Worthing), do the thinking for them. Sanity-check places against the map and gently correct.
5. **Offer options when the destination is open.** If they have not pinned an exact route, give 2-3 distinct options (e.g. fastest / most scenic / most fun) with a one-line pitch each, then build the GPX for the one they pick.
6. **Always produce a valid GPX.** That is the deliverable. Everything else (time, weather, kit) wraps around it.
7. **Never bake in unexplained stops.** Route-shaping via-points (used to bend the line onto nicer roads) are invisible by default and are not the same as stops. Any marked stop (cafe, water, food, view, viewpoint, refuel) must be deliberate, named, listed in the brief, and confirmed with the user, never silently dropped into the GPX. If you shaped the route through a town, say so and let the user decide whether it becomes a stop.
8. **Never anchor a route on a town or place name.** Geocoding a settlement returns its *centre*, so forcing it as a via-point makes the route dive into the town centre and back out, a pointless dog-leg. Do not use place-name geocodes as routing via-points. Geocode only the genuine start, the destination, and explicitly requested stops. To bias the line toward a feature (coast, ridge, valley, a named road or cycleway), use a coordinate that sits *on that feature's road/path* in the direction of travel, taken from the map, not a town centroid. After routing, inspect the line: if it darts into somewhere and back along nearly the same road, remove that via and re-route. Pass through towns by letting the engine route through them, never by pinning their centre.
9. **Personalise to the rider.** Use what Claude already knows about this person (memory, past chats, Strava) and a short quiz to fill the rest, then build to their preferences, not a generic route. Store the profile so the quiz runs once. Apply preferences lightly and visibly, respect privacy (do not parrot memory), and always let the user skip or correct.

## Step 0 — Read the request

Work out, from whatever the user said:

- **Activity** — cycle (road / gravel / MTB / e-bike), run, hike, walk, paddleboard, kayak, swim, freedive/spearfishing approach, or other. Infer if unstated (e.g. "ride" = road cycle unless context says otherwise).
- **Anchor** — a start point, a destination, both, or neither. "Near me" / "from home" needs their location: use the `user_location_v0` tool, or ask once if it matters and is unknown.
- **Target** — a distance ("100km"), a duration ("about 2 hours"), a destination ("the best tacos"), or just a vibe ("scenic loop"). One of these is usually present; if truly nothing, propose something sensible for the activity.
- **Structure** — loop, out-and-back, point-to-point, **ride/run out and train back**, or **train out then loop/return**. See `references/route-structures.md`.
- **Date / time** — for the weather pull. Default to the next suitable day if unstated; confirm if it changes the plan.

Do not interrogate. Make smart assumptions, state them inline, and proceed. Only ask a clarifying question if getting it wrong would waste real work (e.g. activity genuinely ambiguous, or start point unknown and unguessable).

## Step 1 — Pull Strava context for pace

Before estimating any time, get the user's real numbers. See `references/strava.md` for exact tool calls. In short: load recent activities of the matching sport type, compute their typical moving speed (and a sensible range), and note typical distance/elevation so the plan fits their form. If Strava is unavailable or has no data for that sport, fall back to the documented defaults in `references/activities.md` and say so.

## Step 1.5 — Know the rider (preferences)

Build the route around who this person is. This is what makes the skill personal, and it matters most when it is shared publicly and the user is a stranger. Full detail in `references/rider-profile.md`.

1. **Load any saved profile:** `python scripts/profile.py show`. If one exists, use it, skip the quiz, and only ask "anything different for this ride?".
2. **First use: gather what Claude already knows before asking.** Use in-context memory about the user, mine past chats with `conversation_search` / `recent_chats` for stated likes and dislikes (coffee, hills, traffic, scenery, food), and use Strava (Step 1) for distance/terrain comfort. Pre-fill the profile, then tell the user in a line what you assumed so they can correct it. Apply memory lightly; never recite sensitive details.
3. **Quiz only the gaps.** Run a short adaptive quiz for what is still unknown. Use the interactive tappable-input tool if available (easier on mobile), otherwise prose. Keep it brief, let them skip with sensible defaults, and do not ask what you already inferred. Questions and options are in `references/rider-profile.md`.
4. **Save it:** `python scripts/profile.py merge '<json>'`, and where memory persists across chats, also remember the durable preferences. Re-quiz only on request.
5. **Apply it everywhere downstream** (terrain, climbing, scenery corridor, surface, traffic tolerance, default stops, structure, sizing). State in one line how their profile shaped the route, so it is visible and correctable.

## Step 2 — Pick the planning mode

- **Land activities** (cycle, run, hike, walk) → routing engine. See `references/routing-engines.md`.
- **Water activities** (paddleboard, kayak, swim, freedive approach) → waypoint plotting, not a routing engine. See `references/water-sports.md`. Wind and tide dominate.

Map the activity to the right engine profile using `references/activities.md`.

## Step 3 — Design the route(s)

1. **Resolve places.** Geocode any named start/destination (`scripts/geo.py geocode "<place>"`). For fuzzy destinations ("best tacos on the west coast", "a nice cafe halfway"), use `web_search` to find real, currently-open spots, then geocode the winner. Quietly fix wrong place names.
2. **Shape for scenery and calm, without dog-legs.** This is the craft. Do not just route A to B, but shape with care:
   - **Try the direct engine route first.** The cycling/foot profiles already favour pleasant, low-traffic roads. Route start to destination and look at what you get before adding anything.
   - **Never use a town or place name as a via-point.** Its geocode is the town centre, which forces an in-and-out detour (golden rule 8). To pull the line onto a feature (coast, ridgeline, valley, a specific cycleway like NCN15), add a via that is a coordinate *on that road or path*, in the direction of travel, read off the map, not a settlement centroid.
   - **Seed ideas, not coordinates, from `web_search`** ("best cycling/running/hiking routes near X", scenic segments, club favourites). Use them to decide which corridor or road to favour, then trust the engine to pass through, or place a single on-route coordinate to bias it.
   - **Inspect every result.** If the line darts into a place and back along nearly the same road, that via is wrong: remove it and re-route. Popular does not always mean scenic or quiet, so weigh it. Prefer adding distance over a busy stretch, but never accept a pointless spur. If a distance/duration was given, tune via-points and loop size until the routed distance lands within ~5%. Build the loop outward then back, or extend an out-and-back turnaround, as needed.
4. **Generate options when open-ended.** For BRouter, request alternatives (`--alternatives 3`) to get genuinely different lines. Present each as a short pitch (distance, climb, character) and let the user choose before the final GPX. For a fixed destination, one well-shaped route is fine.

### Multiple destinations to visit (ordering)

When the user wants to visit several specific places and the order is up to you ("a loop taking in these 6 cafes", "errands hitting all these shops", "ride past these viewpoints"), work out the best order *before* routing:

1. Geocode each place (`scripts/geo.py`).
2. Order them with `scripts/optimize_stops.py --stops "lat,lon,Name; ..."`, adding `--start`/`--end` to pin a depot/home and `--round-trip` for a loop. It returns the shortest visiting order (exact for ≤12 stops) plus a ready-to-use `points` string and a `named_stops` string.
3. Pass its `points` to `route.py --points` to route the real scenic line through them in that order, and its `named_stops` to `route.py --stops` so each is a named, confirmed waypoint. This optimizes order by straight-line distance only — the routing engine still shapes the actual roads. Confirm the stops with the user (Step 3.5) before baking them in.

For a single start→destination route, skip this; it is only for "visit all of these".

## Step 3.5 — Stops (propose, name, confirm)

Stops are a planning decision, not a side effect. Decide them deliberately and put the user in control.

1. **Shaping points are not stops.** The via-points you pass to `route.py --points` only bend the route; by default they are invisible in the GPX. Do not pass `--label-vias` unless the user wants those bends marked.
2. **Propose stops sized to the effort.** On anything long enough to need them, suggest a sensible few: a coffee/food stop, a water/refuel point, a viewpoint or swim spot. Anchor them to real places on the line (use `web_search` for a good cafe/pub at roughly the right distance) and to the user's likely needs (a refuel every ~40-60 km on a long ride, water before exposed sections).
3. **Name them and say what they are.** "Whitstable Harbour (coffee / oysters, ~95 km)", not "Via 2".
4. **Confirm before baking them in.** List the proposed stops in the brief and ask which the user wants, or offer them as quick options. Only the chosen stops go into the GPX, passed as `route.py --stops "lat,lon,Name; ..."`.
5. **If the user names their own stops, use those** and place them as `--stops` (and, if the route must physically detour to reach one, also add it to `--points`).

Always tell the user, in plain words, every waypoint that ends up in the GPX and why.

## Step 4 — Weather for the day

Run `scripts/weather.py` for the route's midpoint (and, for water, the launch point) on the planned date. See `references/weather.md`. Summarise the window the user will be out: temperature, rain chance, wind speed/gusts and direction, and for water, wave height/period. Translate it into advice: headwind on the way out, gusts above a paddleboarding-comfortable threshold, a soaking after 2pm, etc.

## Step 5 — Build the GPX and brief the user

1. Produce the GPX with `scripts/route.py` (land) or `scripts/water_route.py` (water). Pass the Strava-derived speed so the embedded time estimate and optional trackpoint timestamps are the user's own.
2. Save the `.gpx` to `/mnt/user-data/outputs/` and present it with `present_files`.
3. Give a tight brief using the template below.

### Output brief template

```
**<Route name> — <activity>, <distance> km, <elevation gain> m climb**

<One or two lines on character: what makes it scenic/quiet and why this line.>

- Structure: <loop / out-and-back / point-to-point / out + train back>
- Your estimated moving time: <hh:mm> (based on your Strava avg of <x> km/h for <activity>)
- Stops in this GPX: <named stop (what it is, ~km) / "none, just start and finish"> — confirmed with you
- Surface / terrain: <tarmac lanes / gravel / coast path / open water>
- Weather <date>, <window>: <temp>, <rain>, wind <speed> km/h gusting <gust> from <dir><, waves <h> m for water>
- Watch for: <headwind leg / busy crossing / tide window / exposed section>
- Kit: <weather- and activity-appropriate notes>

GPX attached.
```

If you generated several options, list them first with their one-line pitches, build the GPX only for the chosen one (or all, if asked).

## Adapting to anything

- **Unknown activity speed** → see defaults in `references/activities.md`.
- **Ride/run out, train back** → route point-to-point to a station near the far end; find stations with `web_search`. See `references/route-structures.md`.
- **Multi-day / bikepacking** → split into day legs, one GPX per day, with overnight stops.
- **Destination is a vibe, not a place** → search for the real POI, confirm it exists and is open, then route to it.
- **User is wrong** → correct kindly and proceed with the right facts (e.g. "Rampion wind farm is off Worthing, not Brighton, so I have launched you from West Worthing").

## Future: direct upload

When the user provides Strava and Suunto API keys, routes can be pushed to their account/device directly instead of (or as well as) a GPX file. Until then, GPX is the deliverable. Keep the GPX generation as the source of truth so upload is a thin layer on top later.



## Example requests this skill handles

Exact, vague, and slightly-wrong requests all belong here. A non-exhaustive sample:

- "Plan me a 100 km scenic cycle loop from home on Saturday, give me a few options."
- "Quietest 60 km road ride to the coast, I'll train back."
- "Gravel loop near the South Downs, ~3 hours, lots of climbing."
- "Scenic 15 km trail run near Box Hill." / "Flat 5 km loop from home, roads only."
- "Best big-view day hike within 2 hours of London."
- "Paddle to the wind farm off West Worthing and back, is it safe Saturday?"
- "Plan a ride to the best tacos on the west coast." (find the real POI, then route)
- "I want to ride 100 km, no idea where, you pick." / "Something fun and hilly for Sunday."
- "I'm in Lisbon next week, plan me a scenic morning run."
- "Update my route preferences." / "Ignore my profile for this one."

If the request is loose, infer sensibly, offer options where the destination is open, and confirm stops before building.

## Reference files
- `references/routing-engines.md` — OpenRouteService and BRouter: profiles, avoiding busy roads, via-points, alternatives, API keys.
- `references/activities.md` — per-activity engine profile, default speeds, and how to read Strava for each.
- `references/water-sports.md` — paddleboard/kayak/swim/freedive planning, wind/tide limits, coastal hugging, safety.
- `references/weather.md` — Open-Meteo land and marine forecast usage and how to turn it into advice.
- `references/strava.md` — which Strava MCP tools to call and how to derive pace and form.
- `references/rider-profile.md` — the preferences profile, the quiz, how to infer from memory/past chats/Strava, and how each preference shapes the route.
- `references/route-structures.md` — loop, out-and-back, point-to-point, out-and-train-back, train-out-loop.
