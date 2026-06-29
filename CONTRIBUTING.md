# Contributing

Thanks for your interest in improving Route Planner! This repo is a Claude Skill plus
two small Python scripts, so contributing is lightweight.

## Ground rules

- **No runtime dependencies.** The scripts are standard-library only on purpose, so the
  skill works anywhere Python 3.9+ runs with no `pip install`. Please keep it that way.
- **Tests must pass.** Run them before opening a PR:
  ```bash
  cd route-planner
  python3 -m unittest discover -s tests -v
  ```
- **Keep the skill honest.** If you change behavior, update `route-planner/SKILL.md`,
  the `README.md`, and `references/algorithm.md` so the docs match the code.

## Ideas worth contributing

- Road-distance support via a routing API (behind an optional flag/key).
- Additional output formats (GPX, Apple Maps / Waze links).
- A vehicle-routing (multi-vehicle / capacity / time-window) variant.

## Building your own variant

This repo is meant to be forked. Edit `route-planner/SKILL.md` — especially its
`description`, which is what tells Claude when to use the skill — then push and share
your link. See the README's "Make it your own" section.
