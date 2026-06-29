#!/usr/bin/env python3
"""Fetch a forecast for a point and date from Open-Meteo (no API key).

Usage:
  python weather.py --lat 50.809 --lon -0.395 --date 2026-07-10 --marine
  python weather.py --lat 51.53 --lon -0.04 --date 2026-07-01 --from 08:00 --to 12:00

Prints a JSON summary of the requested window: temperature, rain chance,
wind speed/gusts/direction, and (with --marine) wave height/period. Includes
simple flags (e.g. high_wind, rain_likely) the planner can turn into advice.
Open-Meteo forecasts run ~16 days ahead; beyond that it returns nothing.
"""
import json
import argparse
import urllib.parse
import urllib.request

DIRS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _bearing_to_compass(deg):
    return DIRS[int((deg % 360) / 22.5 + 0.5) % 16]


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "alpn-route-planner/1.0"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _window(times, frm, to):
    idx = []
    for i, t in enumerate(times):
        hhmm = t[11:16]
        if frm <= hhmm <= to:
            idx.append(i)
    return idx or list(range(len(times)))


def land(lat, lon, date, frm="06:00", to="20:00"):
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,precipitation,precipitation_probability,"
                  "wind_speed_10m,wind_gusts_10m,wind_direction_10m,weather_code",
        "wind_speed_unit": "kmh", "timezone": "auto",
        "start_date": date, "end_date": date,
    }
    d = _get("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params))
    h = d.get("hourly")
    if not h:
        return {"available": False, "reason": "no land forecast (date out of range?)"}
    idx = _window(h["time"], frm, to)
    temps = [h["temperature_2m"][i] for i in idx]
    pop = [h["precipitation_probability"][i] for i in idx]
    rain = [h["precipitation"][i] for i in idx]
    wind = [h["wind_speed_10m"][i] for i in idx]
    gust = [h["wind_gusts_10m"][i] for i in idx]
    wdir = [h["wind_direction_10m"][i] for i in idx]
    avg_dir = sum(wdir) / len(wdir)
    return {
        "available": True, "window": f"{frm}-{to}",
        "temp_c": {"min": min(temps), "max": max(temps)},
        "rain_chance_pct_max": max(pop),
        "rain_mm_total": round(sum(rain), 1),
        "wind_kmh": {"avg": round(sum(wind) / len(wind)), "max": round(max(wind))},
        "gust_kmh_max": round(max(gust)),
        "wind_from": _bearing_to_compass(avg_dir),
        "flags": {
            "rain_likely": max(pop) >= 50 or sum(rain) >= 2,
            "high_wind": max(gust) >= 40,
            "cold": min(temps) <= 5,
            "hot": max(temps) >= 28,
        },
    }


def marine(lat, lon, date, frm="06:00", to="20:00"):
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": "wave_height,wave_direction,wave_period,wind_wave_height",
        "timezone": "auto", "start_date": date, "end_date": date,
    }
    try:
        d = _get("https://marine-api.open-meteo.com/v1/marine?" + urllib.parse.urlencode(params))
    except Exception as e:  # noqa: BLE001
        return {"available": False, "reason": f"marine fetch failed: {e}"}
    h = d.get("hourly")
    if not h or not h.get("wave_height") or all(v is None for v in h["wave_height"]):
        return {"available": False, "reason": "no marine data for this point (too far inland?)"}
    idx = _window(h["time"], frm, to)
    wh = [h["wave_height"][i] for i in idx if h["wave_height"][i] is not None]
    wp = [h["wave_period"][i] for i in idx if h["wave_period"][i] is not None]
    wdir = [h["wave_direction"][i] for i in idx if h["wave_direction"][i] is not None]
    if not wh:
        return {"available": False, "reason": "no marine data in window"}
    avg_dir = sum(wdir) / len(wdir) if wdir else 0
    return {
        "available": True,
        "wave_height_m": {"avg": round(sum(wh) / len(wh), 2), "max": round(max(wh), 2)},
        "wave_period_s": round(sum(wp) / len(wp), 1) if wp else None,
        "wave_from": _bearing_to_compass(avg_dir),
        "flags": {"choppy": max(wh) >= 0.6, "big": max(wh) >= 1.0},
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--from", dest="frm", default="06:00")
    ap.add_argument("--to", default="20:00")
    ap.add_argument("--marine", action="store_true")
    a = ap.parse_args()

    out = {"land": land(a.lat, a.lon, a.date, a.frm, a.to)}
    if a.marine:
        out["marine"] = marine(a.lat, a.lon, a.date, a.frm, a.to)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    _main()
