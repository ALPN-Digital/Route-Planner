#!/usr/bin/env python3
"""Plan a water route (paddleboard / kayak / swim / freedive approach) and write GPX.

No routing engine routes on open water, so we plot the line the user will actually
take (launch -> turnaround/destination -> back, or a coastal hug via via-points)
and densify it for smooth devices. Distance is great-circle along the waypoints.

Usage:
  python water_route.py \
    --points "50.8090,-0.3950; 50.7600,-0.3700" \
    --out-and-back \
    --name "Rampion wind farm and back" \
    --activity paddleboard \
    --speed-kmh 5.5 \
    --start 2026-07-10T09:00:00Z \
    --out /mnt/user-data/outputs/rampion.gpx

--points: launch, then destination/turnaround, plus any coastal via-points.
--out-and-back: append the reversed outbound legs so the user returns to launch.
--speed-kmh: use the user's Strava paddle/kayak/swim average.
Prints a JSON summary.
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gpx import write_gpx  # noqa: E402
from geo import haversine_km  # noqa: E402


def parse_points(s):
    pts = []
    for chunk in s.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        lat, lon = chunk.split(",")
        pts.append((float(lat), float(lon)))
    if len(pts) < 2:
        raise ValueError("Need at least a launch and a destination point.")
    return pts


def densify(points, step_km=0.25):
    """Insert intermediate points so the track is smooth on a device."""
    out = [points[0]]
    for i in range(1, len(points)):
        a, b = points[i - 1], points[i]
        d = haversine_km(a[0], a[1], b[0], b[1])
        n = max(1, int(d / step_km))
        for k in range(1, n + 1):
            f = k / n
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
    return out


def plan(points, out, name="Water route", activity="paddleboard",
         out_and_back=False, speed_kmh=None, start=None, description=None):
    legs = list(points)
    if out_and_back:
        legs = legs + list(reversed(points[:-1]))
    dense = densify(legs)
    wpts = [(points[0][0], points[0][1], "Launch")]
    wpts.append((points[-1][0], points[-1][1], "Turnaround" if out_and_back else "Destination"))
    stats = write_gpx(dense, out, name=name, activity=activity, waypoints=wpts,
                      speed_kmh=speed_kmh, start_iso=start, description=description)
    stats["out_and_back"] = out_and_back
    return stats


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="Water route")
    ap.add_argument("--activity", default="paddleboard")
    ap.add_argument("--out-and-back", action="store_true")
    ap.add_argument("--speed-kmh", type=float, default=None)
    ap.add_argument("--start", default=None)
    ap.add_argument("--desc", default=None)
    a = ap.parse_args()

    pts = parse_points(a.points)
    stats = plan(pts, a.out, name=a.name, activity=a.activity,
                 out_and_back=a.out_and_back, speed_kmh=a.speed_kmh,
                 start=a.start, description=a.desc)
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    _main()
