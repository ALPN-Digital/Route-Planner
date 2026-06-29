# Install

> Repo: `https://github.com/ALPN-Digital/Route-Planner` (if you forked it, swap in your own URL below).

The skill source is the `route-planner/` folder (its `SKILL.md` is at `route-planner/SKILL.md`). A prebuilt `route-planner.skill` bundle is in the repo root for upload-based installs.

---

## The easiest way: let Claude install it

Paste this to Claude (in Claude Code, Cowork, or any agent with file access):

> Install the route-planner skill from https://github.com/ALPN-Digital/Route-Planner . Read its README and SKILL.md, copy the `route-planner/` folder into my skills directory, then walk me through connecting Strava and adding a routing key.

Claude will read this repo and do the steps below for you. On the Claude apps (claude.ai, desktop, mobile) Claude cannot install skills for you; use the upload method in that section.

---

## Claude Code

Skills are filesystem-based. Clone the repo and copy the skill folder into your skills directory.

Personal (available in every project):

```bash
git clone https://github.com/ALPN-Digital/Route-Planner.git /tmp/route-planner-repo
mkdir -p ~/.claude/skills
cp -r /tmp/route-planner-repo/route-planner ~/.claude/skills/route-planner
```

Project-scoped (shared with a repo via git):

```bash
cp -r /tmp/route-planner-repo/route-planner .claude/skills/route-planner
```

Start a new Claude Code session (top-level skills directories are scanned at startup), then run `/skills` to confirm `route-planner` loaded. Ask it to plan a route, or invoke `/route-planner` directly.

## Cowork

Cowork reads the same SKILL.md format. Either point Cowork at this repo and ask it to install the skill (it will copy the `route-planner/` folder into its skills location), or upload the `route-planner.skill` bundle if your Cowork build supports skill upload.

## Claude apps (claude.ai, desktop, mobile)

1. Download `route-planner.skill` from this repo.
2. In Claude, open Settings, then Capabilities (sometimes labelled Features), then Skills.
3. Upload `route-planner.skill`.
4. Start a chat and ask Claude to plan a route.

Menu names move around; if this does not match, see https://support.claude.com and search "skills".

## Other agents (Cursor, Codex, etc.)

Same idea, different directory:

```bash
# Cursor
cp -r /tmp/route-planner-repo/route-planner ~/.cursor/skills/route-planner
# Codex
cp -r /tmp/route-planner-repo/route-planner ~/.agents/skills/route-planner
```

---

## After installing

1. **Connect Strava** for personalised pace and preferences. In Claude, Settings, then Connectors, find Strava, Connect, and authorise. Optional but recommended.
2. **Add a routing key (optional, free).** Paste an OpenRouteService key into `route-planner/scripts/route.py` (the `EMBEDDED_ORS_API_KEY` line) or set an `ORS_API_KEY` environment variable. Without it the skill uses BRouter, no key needed. Full walkthrough in [ONBOARDING.md](ONBOARDING.md).
3. **First request runs a short preference quiz** and saves your rider profile, so it only asks once.

## Verify it works

Ask: "Plan me a quiet 20 km cycle loop from home." You should get a GPX file, a time estimate, and a weather note. If routing fell back to BRouter, your ORS key is missing or still the placeholder (that is fine; BRouter is good).

## Rebuild the bundle from source

If you edit the skill, rebuild `route-planner.skill` by zipping the `route-planner/` folder so `SKILL.md` sits at the top of the archive, then rename it to `route-planner.skill`:

```bash
cd route-planner-repo && zip -r ../route-planner.skill route-planner -x "*__pycache__*"
```
