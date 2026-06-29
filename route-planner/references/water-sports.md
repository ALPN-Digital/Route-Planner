# Water sports planning

Routing engines do not route on water. Plot the actual line with `scripts/water_route.py` and let wind, tide and waves drive the plan. Safety comes before scenery here.

## Workflow

1. Geocode or web-search the launch point and the destination/turnaround (a wind farm, headland, island, reef, beach). For named offshore features, search for their coordinates and confirm them; correct the user if the feature is off a different town than they said.
2. Decide the line: straight out-and-back for open water, or a coastal hug via via-points if following a shore. Pass `--out-and-back` to auto-return to the launch.
3. Use the user's Strava paddle/kayak/swim average for `--speed-kmh`. If none, use the defaults in `activities.md` and flag the estimate as rough.
4. Always pull marine + wind weather (`weather.py --marine`) for the launch point and planned window.

## Wind and wave thresholds (rules of thumb, not gospel)

- **Paddleboard:** comfortable below ~15 km/h wind. 15-25 km/h is hard work and risky offshore, especially with any offshore component. Above ~25 km/h gusts, advise against going out, or keep it short and inshore. Offshore wind (blowing from land to sea) is the danger case: it pushes you out and is deceptively calm at the beach. Flag wind direction relative to the coast explicitly.
- **Sea kayak:** more wind-tolerant but still flag gusts above ~30 km/h and waves above ~0.8 m for less experienced paddlers.
- **Open-water swim / freedive:** flag waves above ~0.5 m, any offshore wind, and cold water. Mention water temperature if available and wetsuit guidance.

## Tides and currents

Open-Meteo does not give tide times. For coastal and estuary plans, tell the user to check tide tables (search "tide times <place> <date>") and prefer launching to paddle/swim *into* wind or current on the way out so the return is assisted, not the reverse. Note slack-water windows for anything near strong tidal races.

## Always include in the brief

- Wind speed, gusts and direction relative to the coast, with a plain go / caution / no-go read.
- Wave height and period for the window.
- A reminder on safety kit appropriate to the activity (leash and buoyancy aid for SUP, etc.) and to tell someone the plan.
- The fact that offshore distances feel longer than they look, and that the return leg is the one to budget energy for.
