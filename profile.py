#!/usr/bin/env python3
"""Store and read a rider preference profile so routes are personal and the
quiz only runs once.

Profile location: $ROUTE_PLANNER_PROFILE, else ~/.route-planner/rider-profile.json

CLI:
  python profile.py show                       # print current profile (or {})
  python profile.py merge '{"terrain":"hilly"}' # deep-merge JSON into profile
  python profile.py set stops=coffee,tacos      # set one field (lists via commas)
  python profile.py clear                       # wipe the profile

Importable: load_profile(), save_profile(d), merge_profile(d).
"""
import os
import re
import sys
import json

LIST_FIELDS = {"scenery", "stops", "avoid"}


def _path():
    p = os.environ.get("ROUTE_PLANNER_PROFILE")
    if p:
        return p
    return os.path.join(os.path.expanduser("~"), ".route-planner", "rider-profile.json")


def load_profile():
    try:
        with open(_path(), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_profile(profile):
    path = _path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
    return profile


def merge_profile(patch):
    cur = load_profile()

    def deep(a, b):
        for k, v in b.items():
            if isinstance(v, dict) and isinstance(a.get(k), dict):
                deep(a[k], v)
            else:
                a[k] = v
        return a

    return save_profile(deep(cur, patch))


def _parse_value(field, raw):
    if field in LIST_FIELDS:
        return [x.strip() for x in raw.split(",") if x.strip()]
    low = raw.lower()
    if low in ("true", "false"):
        return low == "true"
    if re.fullmatch(r"-?\d+(\.\d+)?", raw):
        return float(raw) if "." in raw else int(raw)
    return raw


def _main(argv):
    if not argv:
        print(__doc__)
        return 1
    cmd = argv[0]
    if cmd == "show":
        print(json.dumps(load_profile(), indent=2, ensure_ascii=False))
        return 0
    if cmd == "merge":
        patch = json.loads(argv[1])
        print(json.dumps(merge_profile(patch), indent=2, ensure_ascii=False))
        return 0
    if cmd == "set":
        out = {}
        for pair in argv[1:]:
            k, _, v = pair.partition("=")
            out[k.strip()] = _parse_value(k.strip(), v)
        print(json.dumps(merge_profile(out), indent=2, ensure_ascii=False))
        return 0
    if cmd == "clear":
        save_profile({})
        print("{}")
        return 0
    print("Unknown command:", cmd)
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
