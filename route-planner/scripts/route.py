#!/usr/bin/env python3
"""Plan a land route (cycle / run / hike / walk) and write a GPX.

Engine selection:
  - OpenRouteService if ORS_API_KEY is set (best avoid-busy-road controls).
  - BRouter otherwise (no key; great quiet/scenic cycling + hiking; alternatives).

Usage:
  python route.py \
    --activity cycling-road \
    --points "51.5363,-0.0395; 51.50,-0.10; 51.5363,-0.0395" \
    --name "Sunday loop" \
    --speed-kmh 24 \
    --start 2026-07-01T08:00:00Z \
    --avoid highways,ferries \
    --alternatives 1 \
    --out /mnt/user-data/outputs/sunday-loop.gpx

--points is "lat,lon" pairs separated by ";" (start, optional vias, end).
--activity is a friendly name (see ACTIVITY_MAP) or a raw engine profile.
--alternatives N (BRouter only) writes N variants as <out>-1.gpx, <out>-2.gpx ...
Prints a JSON summary (distance, climb, engine, time) to stdout.
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpx import write_gpx  # noqa: E402

# OpenRouteService key. Optional: leave the placeholder and the skill uses
# BRouter (no key needed). To enable ORS routing, either paste your free key
# below (get one at https://openrouteservice.org/dev/#/signup) or set an
# ORS_API_KEY environment variable, which takes precedence.
PLACEHOLDER_ORS_KEY = "YOUR_OPENROUTESERVICE_API_KEY"
EMBEDDED_ORS_API_KEY = PLACEHOLDER_ORS_KEY
ORS_API_KEY = os.environ.get("ORS_API_KEY") or EMBEDDED_ORS_API_KEY


def _have_ors_key():
    return bool(ORS_API_KEY) and ORS_API_KEY != PLACEHOLDER_ORS_KEY


# Friendly activity -> (ORS profile, BRouter profile)
ACTIVITY_MAP = {
    "cycling": ("cycling-regular", "trekking"),
    "cycling-road": ("cycling-road", "trekking"),
    "cycling-fast": ("cycling-road", "fastbike"),
    "cycling-gravel": ("cycling-regular", "gravel"),
    "cycling-mountain": ("cycling-mountain", "mtb"),
    "cycling-electric": ("cycling-electric", "trekking"),
    "running": ("foot-walking", "hiking-beta"),
    "walking": ("foot-walking", "hiking-beta"),
    "hiking": ("foot-hiking", "hiking-beta"),
}


def parse_points(s):
    pts = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        lat, lon = chunk.split(",")
        pts.append((float(lat), float(lon)))
    if len(pts) < 2:
        raise ValueError("Need at least a start and an end point.")
    return pts


# avoid_features ORS accepts per profile family. highways/tollways are
# driving-only; cycling/foot profiles already avoid trunk roads inherently.
_AVOID_BY_FAMILY = {
    "driving": {"highways", "tollways", "ferries", "fords"},
    "cycling": {"ferries", "fords", "steps"},
    "foot": {"ferries", "fords", "steps"},
}


def _sanitise_avoid(profile, avoid):
    if not avoid:
        return []
    family = profile.split("-", 1)[0]
    allowed = _AVOID_BY_FAMILY.get(family, set())
    return [a for a in avoid if a in allowed]


def _ors(profile, points, avoid):
    if not _have_ors_key():
        raise RuntimeError("No OpenRouteService key set. Add one or use BRouter (default).")
    key = ORS_API_KEY
    url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"
    body = {"coordinates": [[lon, lat] for (lat, lon) in points], "elevation": True}
    clean_avoid = _sanitise_avoid(profile, avoid)
    if clean_avoid:
        body["options"] = {"avoid_features": clean_avoid}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": key,
        "Content-Type": "application/json",
        "Accept": "application/geo+json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            gj = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"ORS HTTP {e.code}: {detail}") from None
    feat = gj["features"][0]
    coords = feat["geometry"]["coordinates"]  # [lon, lat, ele]
    pts = [(c[1], c[0], c[2]) if len(c) > 2 else (c[1], c[0]) for c in coords]
    summ = feat["properties"].get("summary", {})
    return pts, {"engine": "openrouteservice", "engine_distance_km": round(summ.get("distance", 0) / 1000, 2),
                 "engine_duration_h": round(summ.get("duration", 0) / 3600, 2)}


def _brouter(profile, points, alt_idx=0):
    lonlats = "|".join(f"{lon},{lat}" for (lat, lon) in points)
    url = ("https://brouter.de/brouter?"
           f"lonlats={lonlats}&profile={profile}&alternativeidx={alt_idx}&format=geojson")
    req = urllib.request.Request(url, headers={"User-Agent": "alpn-route-planner/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        gj = json.loads(resp.read().decode("utf-8"))
    feat = gj["features"][0]
    coords = feat["geometry"]["coordinates"]  # [lon, lat, ele]
    pts = [(c[1], c[0], c[2]) if len(c) > 2 else (c[1], c[0]) for c in coords]
    props = feat.get("properties", {})
    dist = props.get("track-length")
    secs = props.get("total-time")
    return pts, {"engine": "brouter", "profile": profile,
                 "engine_distance_km": round(float(dist) / 1000, 2) if dist else None,
                 "engine_duration_h": round(float(secs) / 3600, 2) if secs else None}


def choose_engine(explicit, alternatives):
    """ORS for single shaped routes (best avoid-busy-road control); BRouter when
    several distinct options are wanted, since it returns genuinely different lines."""
    if explicit and explicit != "auto":
        return explicit
    if alternatives and alternatives > 1:
        return "brouter"
    return "ors" if _have_ors_key() else "brouter"


def plan(activity, points, name, out, speed_kmh=None, start=None,
         avoid=None, alternatives=1, description=None, engine="auto",
         stops=None, label_vias=False, start_name="Start", finish_name="Finish"):
    ors_prof, br_prof = ACTIVITY_MAP.get(activity, (activity, activity))
    eng = choose_engine(engine, alternatives)
    results = []

    n = max(1, alternatives)
    if eng == "brouter":
        for i in range(n):
            pts, meta = _brouter(br_prof, points, alt_idx=i)
            wpts = _waypoints(points, stops=stops, label_vias=label_vias,
                              start_name=start_name, finish_name=finish_name)
            suffix = "" if n == 1 else f"-{i + 1}"
            path = out if n == 1 else out.rsplit(".gpx", 1)[0] + f"{suffix}.gpx"
            stats = write_gpx(pts, path, name=f"{name}{(' #' + str(i + 1)) if n > 1 else ''}",
                              activity=activity, waypoints=wpts,
                              speed_kmh=speed_kmh, start_iso=start, description=description)
            stats.update(meta)
            results.append(stats)
    else:  # ORS, single shaped route
        pts, meta = _ors(ors_prof, points, avoid)
        wpts = _waypoints(points, stops=stops, label_vias=label_vias,
                          start_name=start_name, finish_name=finish_name)
        stats = write_gpx(pts, out, name=name, activity=activity, waypoints=wpts,
                          speed_kmh=speed_kmh, start_iso=start, description=description)
        stats.update(meta)
        results.append(stats)
    return results


def _waypoints(points, stops=None, label_vias=False,
               start_name="Start", finish_name="Finish"):
    """Build the GPX waypoint list.

    By default only Start and Finish are marked. Route-shaping points passed in
    `points` are used to bend the line and are NOT emitted as waypoints unless
    `label_vias=True`. Deliberate, named stops (cafe, water, view, lunch) come in
    via `stops` as (lat, lon, name) and are always shown with their real name.
    """
    wpts = [(points[0][0], points[0][1], start_name)]
    if label_vias:
        for j, via in enumerate(points[1:-1], 1):
            wpts.append((via[0], via[1], f"Via {j}"))
    for s in (stops or []):
        wpts.append((s[0], s[1], s[2] if len(s) > 2 else "Stop"))
    wpts.append((points[-1][0], points[-1][1], finish_name))
    return wpts


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--activity", required=True)
    ap.add_argument("--points", required=True)
    ap.add_argument("--name", default="Route")
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed-kmh", type=float, default=None)
    ap.add_argument("--start", default=None)
    ap.add_argument("--avoid", default=None, help="comma list: highways,ferries,steps,tollways")
    ap.add_argument("--alternatives", type=int, default=1)
    ap.add_argument("--engine", default="auto", choices=["auto", "ors", "brouter"])
    ap.add_argument("--stops", default=None,
                    help='named stops as "lat,lon,Name; lat,lon,Name" (markers only)')
    ap.add_argument("--label-vias", action="store_true",
                    help="also mark the route-shaping points as Via 1, Via 2, ...")
    ap.add_argument("--start-name", default="Start")
    ap.add_argument("--finish-name", default="Finish")
    ap.add_argument("--desc", default=None)
    a = ap.parse_args()

    pts = parse_points(a.points)
    avoid = [x.strip() for x in a.avoid.split(",")] if a.avoid else None
    stops = None
    if a.stops:
        stops = []
        for chunk in a.stops.split(";"):
            chunk = chunk.strip()
            if not chunk:
                continue
            parts = [p.strip() for p in chunk.split(",")]
            stops.append((float(parts[0]), float(parts[1]),
                          ",".join(parts[2:]) if len(parts) > 2 else "Stop"))
    res = plan(a.activity, pts, a.name, a.out, speed_kmh=a.speed_kmh,
               start=a.start, avoid=avoid, alternatives=a.alternatives,
               description=a.desc, engine=a.engine, stops=stops,
               label_vias=a.label_vias, start_name=a.start_name, finish_name=a.finish_name)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    _main()
