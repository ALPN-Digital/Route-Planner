# Instructions for Claude (and other AI agents)

If a user points you at this repository and asks you to install or set up the route planner, do the following.

## What this repo is

A Claude Agent Skill called **route-planner** that plans scenic, low-traffic routes for cycling, running, hiking, walking and water sports, and outputs a GPX. The skill source is the `route-planner/` folder; its entry point is `route-planner/SKILL.md`.

## Install it

1. Determine the surface you are running on:
   - **Filesystem agent (Claude Code, Cowork, Cursor, Codex):** copy the `route-planner/` folder into the skills directory.
     - Claude Code personal: `~/.claude/skills/route-planner`
     - Claude Code project: `.claude/skills/route-planner`
     - Cursor: `~/.cursor/skills/route-planner`; Codex: `~/.agents/skills/route-planner`
   - **Claude apps (claude.ai/desktop/mobile):** you cannot install skills yourself. Tell the user to download `route-planner.skill` and upload it under Settings, Capabilities, Skills.
2. After copying, tell the user to start a new session so the skill is detected.
3. Read `route-planner/SKILL.md` so you understand the workflow.

## Help the user finish setup

- Offer to connect Strava (Settings, Connectors, Strava) so route times use their real pace.
- Offer to add a free OpenRouteService key (paste into `route-planner/scripts/route.py` `EMBEDDED_ORS_API_KEY`, or set `ORS_API_KEY`). Without it, routing uses BRouter, which needs no key. See `ONBOARDING.md`.
- Explain that the first route request runs a short preference quiz and saves a rider profile.

## Then use it

Follow `route-planner/SKILL.md`. Honour its rules: scenic and quiet over fast and direct, never anchor routes on town-centre coordinates, confirm stops before adding them, personalise to the rider, and always check the weather for the planned day. See `examples/PROMPTS.md` for the range of requests it handles.

## Do not

- Do not commit a user's personal `rider-profile.json` or any real API key. The `.gitignore` already excludes them.
- Do not hardcode the user's location or preferences into the skill; those live in the saved profile.
