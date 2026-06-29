# Strava: deriving pace and form

The Strava MCP tools are deferred. Load them first with `tool_search` (e.g. query "strava activities"), then call them. If Strava is not connected or returns nothing for the sport, fall back to `activities.md` defaults and tell the user the estimate is generic.

## Tools and how to use them

- `Strava:get_athlete_profile` — confirms the athlete and units.
- `Strava:list_activities` — the workhorse. Pull recent activities, filter to the `sport_type` that matches the planned activity (see the mapping in `activities.md`), and read `distance`, `moving_time`, and `total_elevation_gain`.
- `Strava:get_activity_streams` / `Strava:get_activity_performance` — for a representative recent effort, to see how pace held on climbs vs flat if you need a finer estimate.
- `Strava:get_athlete_zones` — optional, for effort-based pacing on a hard plan.

## Deriving the number to pass to the scripts

1. Take the last ~5-15 activities of the matching sport type with sensible distances (ignore 1km test rides and indoor sessions).
2. Compute moving speed for each: `distance_km / (moving_time_s / 3600)`.
3. Use the median as the planning speed, and note a min-max range for the brief.
4. Adjust for the specific plan: if the planned route climbs far more than their typical outing, bias the speed down; if it is flatter, up.
5. Pass that speed to `route.py --speed-kmh` or `water_route.py --speed-kmh` so the embedded time estimate and trackpoint timestamps are the user's own.

## Using Strava for more than pace

- **Typical distance/elevation** tells you what "a normal ride/run for me" is, which helps when the user is vague ("a decent ride").
- **Recent routes / heatmap intuition** — if the user's history clusters in an area, lean on familiar-but-fresh terrain rather than sending them somewhere random.
- For water sports especially, their paddle/kayak/swim history is the only reliable basis for a time estimate, so always check it before quoting a duration for the wind-farm-and-back type plan.
