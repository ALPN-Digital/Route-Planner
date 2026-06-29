# Route Planner (a Claude skill)

An expert, multi-activity route planner for Claude. Ask it for a ride, run, hike, walk or paddle in plain English and it plans a scenic, low-traffic route, sizes the effort to your own fitness from Strava, checks the weather for the day, and hands back a GPX you can load straight onto your device.

It works for cycling (road, gravel, MTB, e-bike), running, hiking, walking, and water sports (paddleboard, kayak, swim, freedive approaches), anywhere in the world.

## What makes it different

- **Scenic and quiet by default.** It favours country lanes, coast, woodland and cycleways, and actively avoids busy roads and the cycle-paths-beside-motorways trap.
- **Your pace, not a generic one.** It reads your Strava history to estimate time for the activity.
- **It learns your preferences.** On first use it draws on what Claude already knows about you and runs a short quiz (hills or flat, coffee stops, scenery you like, traffic tolerance), then remembers it.
- **Weather-aware.** It checks the forecast for the day you are going, including wind and waves for water sports.
- **GPX out.** Valid GPX with your pace baked into the timestamps, ready for Garmin, Wahoo, Suunto, Komoot and the rest.

## Quick start

1. Install the skill (see below).
2. Connect Strava and, optionally, add a free routing key. Full walkthrough in **[ONBOARDING.md](ONBOARDING.md)**.
3. Ask Claude something like:
   - "Plan me a 100 km scenic cycle loop from home on Saturday, with a couple of options."
   - "Route me a quiet 15 km trail run near Box Hill."
   - "Paddle to the wind farm off West Worthing and back."

On the first request it will set up your rider profile, then build the route. More examples in [examples/PROMPTS.md](examples/PROMPTS.md).

## Installing the skill

Full instructions for every surface are in **[INSTALL.md](INSTALL.md)**. The short version:

- **Let Claude do it.** In Claude Code or Cowork, paste: *"Install the route-planner skill from this repo, then help me connect Strava and add a routing key."* Claude reads the repo (see [CLAUDE.md](CLAUDE.md)) and installs it.
- **Claude Code (manual):** clone the repo and copy the `route-planner/` folder into `~/.claude/skills/route-planner`, then start a new session.
- **Claude apps (web, desktop, mobile):** download `route-planner.skill` from this repo and upload it under Settings, Capabilities, Skills.

## What you need

Nothing is strictly required to get a route, but a couple of free add-ons make it much better. The one-time setup is in **[ONBOARDING.md](ONBOARDING.md)**. In short:

| Thing | Needed? | Cost | Why |
|---|---|---|---|
| OpenRouteService key | Optional | Free | Sharpest control over avoiding busy roads. Without it, routing uses BRouter (no key). |
| Strava connection | Recommended | Free | Personal pace and preferences. Without it, sensible defaults are used. |
| Weather (Open-Meteo) | Built in | Free | No key needed. |
| Maps/geocoding (OpenStreetMap) | Built in | Free | No key needed. |
| Suunto / Strava upload | Roadmap | Free | Direct route upload to your device/account. For now the output is a GPX file you import yourself. |

## How it works (under the hood)

- **Routing:** OpenRouteService when a key is present, otherwise BRouter (both produce GPX; BRouter also gives genuinely different alternatives for "give me options" requests).
- **Weather:** Open-Meteo land and marine forecasts.
- **Geocoding:** OpenStreetMap Nominatim.
- **Personalisation:** a stored rider profile plus Strava and Claude's memory of you.

See the `route-planner/references/` files for the full design.

## Privacy

Your rider profile is stored locally as JSON (see `scripts/profile.py`). The skill uses Claude's memory of you only to pre-fill preferences and applies it lightly. You can skip the quiz, correct anything, or clear your profile at any time.

## Roadmap

- Direct upload to Strava and Suunto (currently GPX export).
- Tide windows for coastal water sports.
- Saved favourite routes and home locations.

## Licence

MIT. See [LICENSE](LICENSE).
