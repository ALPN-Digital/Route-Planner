# Onboarding and setup

This is the one-time setup. None of it is strictly required to get a route, but Strava and a routing key make the results much better. Work through it top to bottom; it takes about ten minutes.

## 1. Install the skill

Use the prebuilt bundle in this repo:

- **Claude apps (web, desktop, mobile):** open your Claude settings, find the skills section, and upload `route-planner.skill`.
- **Claude Code or a filesystem setup:** drop the `route-planner/` folder into your skills directory.

If the menus do not match (Anthropic moves things around), the current instructions live at https://docs.claude.com and https://support.claude.com. Search there for "skills".

Once installed, just ask Claude to plan a route and the skill activates on its own.

## 2. Connect Strava (recommended, free)

Strava lets the planner estimate time from *your* real pace and learn your terrain habits.

1. In Claude, open Settings, then Connectors (sometimes called Integrations or Apps).
2. Find Strava and click Connect.
3. You will be sent to Strava to authorise access. Approve it.
4. Done. The skill will read your recent activities to work out your pace per sport.

No Strava account, or prefer not to connect it? The skill falls back to sensible default speeds and simply says so.

## 3. Add a routing key (optional, free)

The skill routes with **BRouter** out of the box, which needs no key and is very good for quiet, scenic cycling and hiking. Adding an **OpenRouteService (ORS)** key unlocks finer control over avoiding busy roads and richer profiles.

To get a free ORS key:

1. Go to https://openrouteservice.org/dev/#/signup and create an account.
2. Sign in to the dashboard and create a token (also called an API key).
3. Copy the key.

Then give it to the skill in one of two ways:

- **Easiest:** open `route-planner/scripts/route.py`, find the line

  ```python
  EMBEDDED_ORS_API_KEY = "YOUR_OPENROUTESERVICE_API_KEY"
  ```

  and paste your key between the quotes. Save the file (and rebuild the bundle if you installed from the `.skill` file).

- **Or, with an environment variable** (keeps the key out of the file):

  ```bash
  export ORS_API_KEY="your-key-here"
  ```

  An `ORS_API_KEY` environment variable always takes precedence over the one in the file.

The ORS free tier is generous for personal use. If you ever hit its daily limit, the skill still works; it just leans on BRouter.

## 4. Things that need no setup

- **Weather** comes from Open-Meteo. No key, no account.
- **Place search and geocoding** come from OpenStreetMap Nominatim. No key. Please do not hammer it; the skill already paces its requests.

## 5. Suunto and Strava upload (not yet, but coming)

Direct upload of finished routes to your Suunto watch or Strava account is on the roadmap. For now the skill gives you a **GPX file**, which every major device and app imports:

- **Garmin:** Garmin Connect, then Training and Planning, then Courses, then Import.
- **Wahoo:** the Wahoo app, Routes, then Add, then import the GPX.
- **Suunto:** the Suunto app, then add the route and sync to the watch.
- **Komoot / Strava:** import the GPX as a route, then send to your device.

When upload arrives you will be able to connect Suunto and push routes straight across; the GPX will still be there as a fallback.

## 6. First run: your rider profile

The first time you ask for a route, the skill builds a short **rider profile** so routes fit you:

- It uses what Claude already knows about you and your Strava history to pre-fill what it can.
- It asks a few quick questions for the rest (hills or flat, scenery you like, whether you stop for coffee or food, how much traffic you will tolerate, surface, and route shape).
- It saves the answers, so it only asks once. Later you can say "update my route preferences" to change them, or "ignore my profile for this one" for a one-off.

That is it. Ask for a route and go.

## Troubleshooting

- **"It used BRouter, not ORS."** Your ORS key is missing or still the placeholder. Re-check step 3. BRouter results are still good.
- **A very long route fails on ORS.** ORS caps route distance on the free tier. The skill prefers BRouter for long rides, which has no cap; ask it to use BRouter.
- **No weather for a far-future date.** Forecasts only run about 16 days ahead. For dates beyond that you will get seasonal guidance instead of an exact forecast.
- **Marine forecast says no data.** That point is too far inland; for water sports, use a launch point on the coast.
