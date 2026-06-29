# Rider profile: knowing the person before building

Routes should fit the rider, not a generic cyclist/runner. This is what separates this skill from a plain router, and it matters most once the skill is shared publicly, where the user may be a stranger Claude knows nothing about yet.

There are two sources of knowledge: **what Claude already knows about this person**, and **a short quiz** that fills the gaps. Always prefer the former and only ask for the rest.

## Profile schema

Stored as JSON via `scripts/profile.py`. Fields (all optional; fill what you learn):

- `terrain` — preferred effort/terrain: `flat` | `rolling` | `hilly` | `mixed`
- `climbing` — `avoid` | `neutral` | `seek` (some riders chase climbs, some dodge them)
- `scenery` — list from: `coast`, `mountains`, `forest`, `countryside`, `rivers`, `canals`, `parks`, `moorland`, `urban`
- `surface` — `tarmac` | `some-gravel` | `trails-ok`
- `traffic_tolerance` — `minimal` (add distance to avoid traffic) | `low` | `moderate`
- `stops` — list from: `coffee`, `bakery`, `lunch`, `tacos`, `pub`, `viewpoint`, `swim`, `photo`, `none`
- `stop_frequency` — `none` | `occasional` | `frequent`
- `structure_pref` — `loop` | `out-and-back` | `point-to-point-train` | `any`
- `distance_comfort_km` / `duration_comfort_h` — usually inferred from Strava, not asked
- `avoid` — free list (e.g. `busy roads`, `big climbs`, `exposed clifftops`, `gravel`, `fords`)
- `notes` — anything else worth remembering

## Step 1: use what Claude already knows (ask nothing yet)

Before any quiz, gather from:

1. **In-context memory** about the user: interests, fitness, what they like and dislike. For example, a memory that the user loves a particular food, chases hills, or hates traffic should pre-fill the profile.
2. **Past conversations** via `conversation_search` and `recent_chats`: search for route, ride, run, coffee, hills, scenic, traffic, and similar, to catch preferences they have voiced before.
3. **Strava** (already pulled for pace) for `distance_comfort_km`, `duration_comfort_h`, and a hint at `terrain` from the elevation in their usual outings.

Pre-fill the profile from these, then tell the user briefly what you assumed so they can correct it (e.g. "I have set coffee and a lunch stop, and biased it to the coast, going on what I know, say if that is off"). Apply memory lightly and naturally; never recite sensitive personal details back, and never block on it.

## Step 2: quiz only the gaps

For anything still unknown (most things, for a brand-new public user), run a short adaptive quiz. Use the interactive tappable-input tool if available (far easier on mobile); otherwise ask in prose. Keep it to a handful of questions, group them, and let the user skip with sensible defaults. Do not re-ask what Step 1 already answered.

Suggested questions and options:

1. **What makes a route great for you?** (multi) — Scenery and quiet, Hard climbing, Flat and fast, A good stop or two, Off-road/adventure.
2. **Hills?** (single) — Love them, Don't mind, Keep it flatter.
3. **Scenery you most want?** (multi) — Coast, Hills/mountains, Forest, Countryside, Rivers/canals, Parks, City/urban.
4. **Stops?** (multi) — Coffee, Bakery, Lunch/food, Pub, Viewpoint, Swim, None, just ride.
5. **Traffic?** (single) — Avoid at all costs (happy to add distance), A bit is fine, Don't care.
6. **Surface?** (single) — Tarmac only, Some gravel is fine, Trails welcome.
7. **Usual shape?** (single) — Loops, Out-and-back, Ride out + train home, Whatever suits.

Distance/duration comfort usually comes from Strava; only ask if there is no history.

## Step 3: save it, and remember it

- Save: `python scripts/profile.py merge '<json>'` (or `set field=value`). On later rides, `python scripts/profile.py show` loads it and you skip the quiz, asking only "anything different for this one?".
- Where the environment persists memory across chats (e.g. claude.ai), also commit the durable preferences to memory so a future session starts informed even without the file.
- Re-quiz only when the user asks to update preferences, or offer it occasionally ("want to tweak your rider profile?").

## Step 4: apply the profile to the route

Preferences must change the output, not just sit in a file:

- `traffic_tolerance: minimal` → lean on BRouter trekking / ORS avoidance, and accept extra distance for quiet. `moderate` → allow faster, more direct lines.
- `climbing: seek` or `terrain: hilly` → do not avoid climbs; bias toward hillier ground and name the big climbs as features. `avoid`/`flat` → favour valley and coastal-flat lines, flag total ascent, keep it gentle.
- `scenery` → choose the corridor accordingly (coast road, forest, river path), using on-route coordinates, never town centroids (golden rule 8).
- `surface` → pick the matching engine profile (`cycling-road`/`trekking` vs `gravel`/`mtb`; foot vs hiking).
- `stops` + `stop_frequency` → propose stops of the right kind at sensible spacing (Step 3.5), and confirm. A `none` rider gets a clean route and no stop nudges.
- `structure_pref` → default to their preferred shape unless the request says otherwise.
- `distance_comfort` → when the request is vague ("a decent ride"), size it to their norm.
- `avoid` → hard constraints; honour them and say how.

Always tell the user, in a line, how their profile shaped this route, so the personalisation is visible and correctable.
