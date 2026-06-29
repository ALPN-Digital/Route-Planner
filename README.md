# Route Planner — a Claude Skill

A ready-to-use [Claude Agent Skill](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
that turns a pile of addresses into an **optimized multi-stop route** with a shareable
Google Maps link. Drop it into Claude Code, claude.ai, or Claude Cowork and ask Claude
to plan a route — it does the geocoding and the route optimization for you.

It also doubles as a **template**: clone it, tweak `route-planner/SKILL.md`, and you
have your own route-planning skill for your own Claude.

```
You:    Plan the most efficient round trip from my office to these 6 client addresses.
Claude: (runs the skill) → ordered stops, total distance, and a Google Maps link.
```

## What's inside

| Path | What it is |
| --- | --- |
| `route-planner/SKILL.md` | The skill definition Claude reads (frontmatter + instructions). |
| `route-planner/scripts/optimize_route.py` | Route optimizer — exact for ≤12 stops, nearest-neighbor + 2-opt + Or-opt heuristic beyond. Standard library only. |
| `route-planner/scripts/geocode.py` | Turns addresses into coordinates via free OpenStreetMap Nominatim. No API key. |
| `route-planner/references/algorithm.md` | How the optimizer works and how to extend it. |
| `route-planner/examples/` | Sample JSON and CSV stop lists. |

No dependencies. No API keys. Python 3.9+ is the only requirement, and routing works
fully offline once stops have coordinates.

## Install it

### Option A — let Claude do it (easiest)

Paste this into **Claude Code**, **claude.ai**, or **Cowork**:

> Install the route-planner skill from https://github.com/ALPN-Digital/Route-Planner
> — clone it and add the `route-planner/` folder to my skills, then plan me a route.

### Option B — Claude Code (manual)

Copy the skill into your project or personal skills directory:

```bash
git clone https://github.com/ALPN-Digital/Route-Planner.git
mkdir -p ~/.claude/skills
cp -r Route-Planner/route-planner ~/.claude/skills/route-planner
```

Use `.claude/skills/` inside a project to scope it to that project instead.
Restart Claude Code and ask it to plan a route — it auto-discovers the skill.

### Option C — claude.ai (Skills)

1. Download this repo as a ZIP (green **Code** button → **Download ZIP**), or zip the
   `route-planner/` folder yourself.
2. In claude.ai go to **Settings → Capabilities → Skills** and upload the
   `route-planner` folder/zip (requires a plan with Skills enabled).

## Use it directly (no Claude needed)

The scripts are useful on their own.

```bash
cd route-planner

# 1) Already have coordinates? Optimize straight away:
python3 scripts/optimize_route.py examples/stops.example.json --start Warehouse --round-trip

# 2) Only have addresses? Geocode first, then optimize (one pipeline):
python3 scripts/geocode.py examples/stops.example.csv --format csv \
  | python3 scripts/optimize_route.py --format json
```

Example output:

```
Optimized route:
  1. Warehouse
  2. Statue of Liberty
  3. Brooklyn Bridge
  4. Empire State
  5. Central Park
  6. Times Square
  7. Warehouse (return)

Total distance: 26.162 km (16.256 mi)
Google Maps:    https://www.google.com/maps/dir/40.7128,-74.006/...
```

### Input format

JSON (a list, or `{ "stops": [...] }`) or CSV with a header row:

```json
{ "stops": [
    { "name": "Warehouse", "lat": 40.7128, "lon": -74.0060 },
    { "name": "Client A",  "address": "11 Wall St, New York, NY" }
] }
```

Each stop needs either `lat` + `lon`, or an `address` to geocode. `name` is optional.

### Optimizer flags

| Flag | Effect |
| --- | --- |
| `--start "Name"` | Pin the first stop (depot / home / current location). |
| `--end "Name"` | Pin the last stop. |
| `--round-trip` | Return to the start at the end. |
| `--json-out` | Emit machine-readable JSON instead of the summary. |
| `--format json\|csv` | Force the input format (auto-detected from file extension otherwise). |

## Make it your own

This repo is meant to be forked. To build your own variant:

1. Edit `route-planner/SKILL.md` — the `description` is what tells Claude *when* to
   use the skill, so make it match your use case (deliveries, field service, sales, …).
2. Swap the distance function in `optimize_route.py` for a routing API if you need real
   drive times (see `references/algorithm.md`).
3. Commit, push, and share your repo link — others can install it the same way.

## How good is the routing?

For 12 stops or fewer the optimizer is **exact** (Held-Karp dynamic programming) — it
returns the provably shortest tour. Beyond that it switches to a near-optimal
heuristic (nearest-neighbor + 2-opt + Or-opt with multi-start) that stays within a few
percent and handles ~100 stops in a few seconds.
Distances are great-circle (straight-line) estimates; the *order* is what's optimized.
For exact drive times, feed the optimized order into a routing API. Details in
[`route-planner/references/algorithm.md`](route-planner/references/algorithm.md).

## License

[MIT](LICENSE) — use it, fork it, ship it.
