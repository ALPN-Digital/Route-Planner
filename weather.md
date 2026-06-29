# Weather

`scripts/weather.py` uses Open-Meteo (no API key). Forecasts run about 16 days ahead; beyond that it returns nothing, so for far-future plans give seasonal context from web search instead and say the precise forecast is not yet available.

## Usage

- Land: `python weather.py --lat <lat> --lon <lon> --date YYYY-MM-DD --from 08:00 --to 12:00`
- Add `--marine` for wave data near the coast.
- Use the route midpoint for land, and the launch point for water. For long point-to-point routes, check both ends if conditions differ.

## Turning numbers into advice

The script returns flags, but the value you add is interpretation:

- **Wind direction matters for the legs.** On an out-and-back, a tailwind out means a headwind home, which is the harder half. Say which leg gets the wind. For cycling, a strong crosswind on an exposed ridge or seafront is worth a warning.
- **Rain timing.** If rain arrives at 2pm, suggest starting earlier. Quote the window, not just a daily chance.
- **Temperature into kit.** Cold plus wind means windproof layers; hot plus a long exposed climb means extra water and an early start.
- **Marine flags into go/no-go.** Combine wave height/period with the wind read from `water-sports.md` for a clear recommendation.

## Caveats

- Marine data only exists near coasts; inland points return "no marine data", which is expected.
- Hourly values are point forecasts; treat them as a guide, and round sensibly in the brief (no false precision).
