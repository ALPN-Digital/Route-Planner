# Contributing

Thanks for your interest in improving the Route Planner skill! It's a Claude Agent
Skill plus a handful of small Python scripts, so contributing is lightweight.

## Ground rules

- **No runtime dependencies.** The scripts are standard-library only on purpose, so the
  skill works anywhere Python 3.9+ runs with no `pip install`. Please keep it that way.
- **Tests must pass.** Run the offline suite before opening a PR:
  ```bash
  cd route-planner
  python3 -m unittest discover -s tests -v
  ```
  These cover the logic that doesn't need the network (GPX building, waypoint rules,
  profile storage, geo math, water-route densifying). The live API calls
  (OpenRouteService, BRouter, Nominatim, Open-Meteo) are exercised manually.
- **Keep the skill honest.** If you change behavior, update `route-planner/SKILL.md`,
  the relevant `route-planner/references/*.md`, and the root docs so they match the code.
- **Never commit secrets or personal data.** No API keys, no `rider-profile.json`. The
  `.gitignore` already excludes them — keep it that way.
- **Rebuild the bundle if you change the skill.** See "Rebuild the bundle from source"
  in [INSTALL.md](INSTALL.md) so `route-planner.skill` stays in sync with the folder.

## Repo layout

- `route-planner/SKILL.md` — the skill entry point (frontmatter + workflow).
- `route-planner/scripts/` — `geo.py`, `route.py`, `water_route.py`, `gpx.py`,
  `weather.py`, `profile.py`.
- `route-planner/references/` — the design docs the skill reads at run time.
- `route-planner/tests/` — the offline test suite.
- `examples/` — example prompts and a sample GPX.

## Ideas worth contributing

- Tide windows for coastal water sports.
- Direct upload to Strava / Suunto (currently GPX export).
- Multi-stop ordering (optimize the *order* of several stops, not just the line A→B).
- More activity profiles and per-activity default speeds.
