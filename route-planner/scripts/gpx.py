#!/usr/bin/env python3
"""Write a valid GPX 1.1 file from a list of track points.

Importable:
    from gpx import write_gpx
    write_gpx(points, "out.gpx", name="My ride", activity="cycling",
              waypoints=[(lat, lon, "Start"), ...],
              speed_kmh=24.0, start_iso="2026-07-01T08:00:00Z")

`points` is a list of (lat, lon) or (lat, lon, ele_m).
If speed_kmh and start_iso are given, each trackpoint gets a <time> so devices
show a pace target / virtual partner. Returns a small stats dict.
"""
import math
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

R_KM = 6371.0088


def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R_KM * math.asin(math.sqrt(a))


def _stats(points):
    dist = 0.0
    gain = 0.0
    has_ele = len(points[0]) >= 3
    for i in range(1, len(points)):
        dist += _haversine_km(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])
        if has_ele:
            d = points[i][2] - points[i - 1][2]
            if d > 0:
                gain += d
    return {"distance_km": round(dist, 2), "elevation_gain_m": round(gain) if has_ele else None}


def write_gpx(points, out_path, name="Route", activity="cycling",
              waypoints=None, speed_kmh=None, start_iso=None, description=None):
    if not points or len(points) < 2:
        raise ValueError("Need at least two track points to build a GPX.")

    stats = _stats(points)
    has_ele = len(points[0]) >= 3

    # Optional timestamps from a constant speed and a start time.
    times = None
    if speed_kmh and start_iso:
        try:
            start = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        except ValueError:
            start = datetime.now(timezone.utc)
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        cum_km = 0.0
        times = [start]
        for i in range(1, len(points)):
            seg = _haversine_km(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])
            cum_km += seg
            secs = (cum_km / speed_kmh) * 3600.0 if speed_kmh else 0.0
            times.append(start + timedelta(seconds=secs))

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<gpx version="1.1" creator="alpn-route-planner" '
                 'xmlns="http://www.topografix.com/GPX/1/1" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'xsi:schemaLocation="http://www.topografix.com/GPX/1/1 '
                 'http://www.topografix.com/GPX/1/1/gpx.xsd">')
    lines.append("  <metadata>")
    lines.append(f"    <name>{escape(name)}</name>")
    desc = description or f"{activity} route, {stats['distance_km']} km"
    lines.append(f"    <desc>{escape(desc)}</desc>")
    lines.append("  </metadata>")

    for wp in (waypoints or []):
        wlat, wlon = wp[0], wp[1]
        wname = wp[2] if len(wp) > 2 else "Waypoint"
        lines.append(f'  <wpt lat="{wlat:.6f}" lon="{wlon:.6f}">')
        lines.append(f"    <name>{escape(str(wname))}</name>")
        lines.append("  </wpt>")

    lines.append("  <trk>")
    lines.append(f"    <name>{escape(name)}</name>")
    lines.append(f"    <type>{escape(activity)}</type>")
    lines.append("    <trkseg>")
    for i, pt in enumerate(points):
        lat, lon = pt[0], pt[1]
        lines.append(f'      <trkpt lat="{lat:.6f}" lon="{lon:.6f}">')
        if has_ele:
            lines.append(f"        <ele>{pt[2]:.1f}</ele>")
        if times is not None:
            lines.append(f"        <time>{times[i].astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</time>")
        lines.append("      </trkpt>")
    lines.append("    </trkseg>")
    lines.append("  </trk>")
    lines.append("</gpx>")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    stats["points"] = len(points)
    stats["path"] = out_path
    if speed_kmh:
        stats["moving_time_h"] = round(stats["distance_km"] / speed_kmh, 2)
    return stats


if __name__ == "__main__":
    # Tiny self-test
    pts = [(51.5363, -0.0395, 10), (51.5400, -0.0350, 12), (51.5450, -0.0300, 15)]
    s = write_gpx(pts, "/tmp/_gpx_selftest.gpx", name="Self test", activity="cycling",
                  waypoints=[(51.5363, -0.0395, "Start")], speed_kmh=24, start_iso="2026-07-01T08:00:00Z")
    print(s)
