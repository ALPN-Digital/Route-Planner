#!/usr/bin/env bash
# Push this folder to the existing GitHub repo ALPN-Digital/Route-Planner.
# Requires GitHub auth already set up (gh auth login, or a PAT/SSH key).
set -euo pipefail
REMOTE="https://github.com/ALPN-Digital/Route-Planner.git"

git init -q
git add .
git commit -qm "Route Planner skill: initial public release" || true
git branch -M main
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# Normal push; if the repo was created with a README it will reject, so fall back to force (safe for a brand-new repo).
git push -u origin main || git push -u origin main --force
echo "Pushed to $REMOTE"
