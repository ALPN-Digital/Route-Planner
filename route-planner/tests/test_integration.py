"""End-to-end integration tests with the network hop mocked.

The skill's live calls (Nominatim, Open-Meteo, BRouter, OpenRouteService) can't
run in CI, so here we feed real-shaped API responses through the actual parsing
and GPX-building code. This proves the request wiring and response handling are
correct end to end — everything except the literal TCP connection.

Run:  cd route-planner && python3 -m unittest discover -s tests
"""
import json
import os
import sys
import unittest
import urllib.request
from unittest import mock
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import geo  # noqa: E402
import weather  # noqa: E402
import route  # noqa: E402


# --- Real-shaped fixtures -------------------------------------------------

NOMINATIM = json.dumps([
    {"place_id": 1, "lat": "51.5363", "lon": "-0.0395",
     "display_name": "Victoria Park, Hackney, London, England, United Kingdom"}
]).encode()

_HOURS = [f"2026-07-01T{h:02d}:00" for h in range(24)]
LAND = json.dumps({
    "hourly": {
        "time": _HOURS,
        "temperature_2m": [12 + (h % 6) for h in range(24)],
        "precipitation": [0.0] * 9 + [0.4, 0.6] + [0.0] * 13,
        "precipitation_probability": [10] * 8 + [55, 60, 40] + [10] * 13,
        "wind_speed_10m": [15 + (h % 5) for h in range(24)],
        "wind_gusts_10m": [30 + (h % 8) for h in range(24)],
        "wind_direction_10m": [225] * 24,  # SW
        "weather_code": [3] * 24,
    }
}).encode()

MARINE = json.dumps({
    "hourly": {
        "time": _HOURS,
        "wave_height": [0.5 + 0.05 * (h % 4) for h in range(24)],
        "wave_direction": [200] * 24,
        "wave_period": [5.0 + 0.1 * (h % 3) for h in range(24)],
        "wind_wave_height": [0.3] * 24,
    }
}).encode()

# BRouter / ORS return GeoJSON with [lon, lat, ele] coordinates.
_COORDS = [[-0.0395, 51.5363, 10.0], [-0.035, 51.540, 12.0],
           [-0.030, 51.545, 18.0], [-0.025, 51.550, 15.0]]
BROUTER = json.dumps({
    "features": [{
        "geometry": {"coordinates": _COORDS},
        "properties": {"track-length": "1875", "total-time": "320"},
    }]
}).encode()
ORS = json.dumps({
    "features": [{
        "geometry": {"coordinates": _COORDS},
        "properties": {"summary": {"distance": 1875.0, "duration": 320.0}},
    }]
}).encode()


class _Resp:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _fake_urlopen(req, timeout=None):
    url = req.full_url if hasattr(req, "full_url") else req
    if "nominatim" in url:
        return _Resp(NOMINATIM)
    if "marine-api.open-meteo" in url:
        return _Resp(MARINE)
    if "api.open-meteo" in url:
        return _Resp(LAND)
    if "brouter" in url:
        return _Resp(BROUTER)
    if "openrouteservice" in url:
        return _Resp(ORS)
    raise AssertionError(f"unexpected URL: {url}")


class TestGeocodeIntegration(unittest.TestCase):
    @mock.patch("time.sleep", lambda *_: None)
    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_geocode_parses_result(self):
        res = geo.geocode("Victoria Park, London")
        self.assertEqual(len(res), 1)
        self.assertAlmostEqual(res[0]["lat"], 51.5363)
        self.assertAlmostEqual(res[0]["lon"], -0.0395)
        self.assertIn("Victoria Park", res[0]["name"])


class TestWeatherIntegration(unittest.TestCase):
    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_land_window_and_flags(self):
        out = weather.land(51.53, -0.04, "2026-07-01", frm="08:00", to="12:00")
        self.assertTrue(out["available"])
        self.assertEqual(out["window"], "08:00-12:00")
        self.assertEqual(out["wind_from"], "SW")
        # The 09:00/10:00 hours carry 55-60% rain probability.
        self.assertTrue(out["flags"]["rain_likely"])
        self.assertIn("min", out["temp_c"])

    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_marine_window_and_flags(self):
        out = weather.marine(50.80, -0.40, "2026-07-01", frm="08:00", to="12:00")
        self.assertTrue(out["available"])
        self.assertEqual(out["wave_from"], "SSW")
        self.assertGreater(out["wave_height_m"]["avg"], 0)


class TestRouteIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = __import__("tempfile").mkdtemp()
        self.out = os.path.join(self.tmp, "r.gpx")

    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_brouter_produces_valid_gpx(self):
        results = route.plan(
            "cycling-road",
            [(51.5363, -0.0395), (51.550, -0.025)],
            "Test ride", self.out, speed_kmh=24, engine="brouter")
        self.assertEqual(len(results), 1)
        stats = results[0]
        self.assertEqual(stats["engine"], "brouter")
        self.assertEqual(stats["points"], 4)
        self.assertGreater(stats["distance_km"], 0)
        dom = minidom.parse(self.out)
        self.assertEqual(len(dom.getElementsByTagName("trkpt")), 4)
        # Start + Finish waypoints by default.
        self.assertEqual(len(dom.getElementsByTagName("wpt")), 2)

    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_brouter_alternatives_write_multiple_files(self):
        out = os.path.join(self.tmp, "alt.gpx")
        results = route.plan(
            "cycling-gravel",
            [(51.5363, -0.0395), (51.550, -0.025)],
            "Options", out, engine="brouter", alternatives=3)
        self.assertEqual(len(results), 3)
        for i in range(1, 4):
            self.assertTrue(os.path.exists(os.path.join(self.tmp, f"alt-{i}.gpx")))

    @mock.patch.object(urllib.request, "urlopen", _fake_urlopen)
    def test_ors_path_with_key(self):
        with mock.patch.object(route, "ORS_API_KEY", "test-key"):
            results = route.plan(
                "cycling-road",
                [(51.5363, -0.0395), (51.550, -0.025)],
                "ORS ride", self.out, engine="ors",
                stops=[(51.545, -0.030, "Coffee")])
        self.assertEqual(results[0]["engine"], "openrouteservice")
        dom = minidom.parse(self.out)
        wpt_names = [w.getElementsByTagName("name")[0].firstChild.data
                     for w in dom.getElementsByTagName("wpt")]
        self.assertIn("Coffee", wpt_names)  # named stop made it into the GPX


if __name__ == "__main__":
    unittest.main()
