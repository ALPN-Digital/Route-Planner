# Activities: profiles, default speeds, and Strava reads

Always prefer a Strava-derived speed (see `strava.md`). The defaults below are fallbacks for when Strava is unavailable or has no history for that sport. Speeds are moving averages on mixed terrain; adjust down for big climbing, headwind, or technical ground.

| Activity | route.py `--activity` | Default speed | Strava sport_type to match |
|---|---|---|---|
| Road cycling | `cycling-road` | 22-26 km/h | Ride |
| Road cycling (fast) | `cycling-fast` | 28-32 km/h | Ride |
| Gravel | `cycling-gravel` | 18-22 km/h | GravelRide / Ride |
| Mountain bike | `cycling-mountain` | 12-16 km/h | MountainBikeRide |
| E-bike | `cycling-electric` | 24-28 km/h | EBikeRide |
| Running | `running` | 9-12 km/h | Run / TrailRun |
| Trail running | `running` | 7-10 km/h | TrailRun |
| Walking | `walking` | 4-5 km/h | Walk |
| Hiking | `hiking` | 3.5-4.5 km/h | Hike |

Water activities use `water_route.py`, not `route.py`:

| Activity | Default speed | Strava sport_type |
|---|---|---|
| Paddleboard (SUP) | 4.5-6 km/h | StandUpPaddling |
| Kayak / canoe | 5-7 km/h | Kayaking / Canoeing |
| Open-water swim | 2.5-3.5 km/h | Swim |
| Freedive / spearfishing approach | 2-4 km/h (surface swim with kit) | Swim / Workout |

Notes:
- For hilly routes, time from flat speed underestimates; add roughly Naismith for foot (1 hour per 600 m of ascent on top of distance time) and pad cycling climbs.
- "Fun" usually means flowing descents, varied terrain, good surfaces and a payoff (a view, a cafe, a swim spot). "Scenic" means coast, hills, water and woods. They overlap but are not identical; ask or infer which the user wants when generating options.
- If the user names an activity you do not have a profile for, pick the nearest profile and say which you used.
