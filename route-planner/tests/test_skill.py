"""Offline tests for the route-planner scripts. Standard library only.

Run with:  cd route-planner && python3 -m unittest discover -s tests

These cover the logic that does not need the network (GPX building, waypoint
rules, profile storage, geo math, water-route densifying). The network calls
(ORS, BRouter, Nominatim, Open-Meteo) are exercised manually, not in CI.
"""
import os
import sys
import tempfile
import unittest
from xml.dom import minidom

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import gpx  # noqa: E402
import route  # noqa: E402
import profile as profile_mod  # noqa: E402
import geo  # noqa: E402
import water_route  # noqa: E402
import optimize_stops  # noqa: E402
import itertools  # noqa: E402
import random  # noqa: E402


class TestGpx(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "t.gpx")

    def test_haversine_known(self):
        # NYC -> LA ~3936 km.
        self.assertAlmostEqual(gpx._haversine_km(40.7128, -74.0060, 34.0522, -118.2437),
                               3936, delta=20)

    def test_write_gpx_is_valid_xml(self):
        pts = [(51.5, -0.1, 10), (51.51, -0.09, 12), (51.52, -0.08, 20)]
        stats = gpx.write_gpx(pts, self.out, name="Test", activity="cycling",
                              waypoints=[(51.5, -0.1, "Start"), (51.52, -0.08, "Finish")])
        dom = minidom.parse(self.out)  # raises if malformed
        self.assertEqual(len(dom.getElementsByTagName("trkpt")), 3)
        self.assertEqual(len(dom.getElementsByTagName("wpt")), 2)
        self.assertEqual(stats["points"], 3)
        self.assertGreater(stats["distance_km"], 0)
        self.assertEqual(stats["elevation_gain_m"], 10)  # +2 then +8

    def test_timestamps_when_speed_and_start(self):
        pts = [(51.5, -0.1), (51.6, -0.1)]
        gpx.write_gpx(pts, self.out, speed_kmh=20, start_iso="2026-07-01T08:00:00Z")
        dom = minidom.parse(self.out)
        times = dom.getElementsByTagName("time")
        self.assertEqual(len(times), 2)
        self.assertTrue(times[0].firstChild.data.endswith("Z"))

    def test_no_timestamps_without_speed(self):
        pts = [(51.5, -0.1), (51.6, -0.1)]
        gpx.write_gpx(pts, self.out)
        self.assertEqual(len(minidom.parse(self.out).getElementsByTagName("time")), 0)

    def test_moving_time(self):
        pts = [(51.0, 0.0), (51.0, 1.0)]  # ~70 km east at this latitude
        stats = gpx.write_gpx(pts, self.out, speed_kmh=20)
        self.assertAlmostEqual(stats["moving_time_h"], stats["distance_km"] / 20, places=2)

    def test_requires_two_points(self):
        with self.assertRaises(ValueError):
            gpx.write_gpx([(1.0, 2.0)], self.out)

    def test_name_is_xml_escaped(self):
        gpx.write_gpx([(0.0, 0.0), (0.1, 0.1)], self.out, name="Tacos & Ale <fast>")
        # Parses cleanly and round-trips the literal text.
        dom = minidom.parse(self.out)
        self.assertIn("Tacos & Ale <fast>",
                      dom.getElementsByTagName("trk")[0].getElementsByTagName("name")[0].firstChild.data)


class TestRoute(unittest.TestCase):
    def test_parse_points(self):
        pts = route.parse_points("51.5,-0.1; 51.6,-0.2 ; 51.7,-0.3")
        self.assertEqual(len(pts), 3)
        self.assertEqual(pts[0], (51.5, -0.1))

    def test_parse_points_needs_two(self):
        with self.assertRaises(ValueError):
            route.parse_points("51.5,-0.1")

    def test_waypoints_default_start_finish_only(self):
        pts = [(0, 0), (1, 1), (2, 2), (3, 3)]
        wpts = route._waypoints(pts)
        self.assertEqual([w[2] for w in wpts], ["Start", "Finish"])

    def test_waypoints_label_vias(self):
        pts = [(0, 0), (1, 1), (2, 2), (3, 3)]
        wpts = route._waypoints(pts, label_vias=True)
        self.assertEqual([w[2] for w in wpts], ["Start", "Via 1", "Via 2", "Finish"])

    def test_waypoints_named_stops(self):
        pts = [(0, 0), (3, 3)]
        wpts = route._waypoints(pts, stops=[(1, 1, "Coffee"), (2, 2, "View")])
        self.assertEqual([w[2] for w in wpts], ["Start", "Coffee", "View", "Finish"])

    def test_sanitise_avoid_by_family(self):
        # highways is driving-only; cycling profiles drop it.
        self.assertEqual(route._sanitise_avoid("cycling-road", ["highways", "ferries"]),
                         ["ferries"])
        self.assertEqual(set(route._sanitise_avoid("driving-car", ["highways", "tollways"])),
                         {"highways", "tollways"})

    def test_choose_engine(self):
        self.assertEqual(route.choose_engine("brouter", 1), "brouter")
        self.assertEqual(route.choose_engine("auto", 3), "brouter")  # alternatives -> brouter
        # With no ORS key configured (CI default), auto falls back to brouter.
        self.assertEqual(route.choose_engine("auto", 1),
                         "ors" if route._have_ors_key() else "brouter")

    def test_activity_map_has_core_activities(self):
        for act in ("cycling-road", "running", "hiking", "cycling-gravel"):
            self.assertIn(act, route.ACTIVITY_MAP)


class TestProfile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self._old = os.environ.get("ROUTE_PLANNER_PROFILE")
        os.environ["ROUTE_PLANNER_PROFILE"] = os.path.join(self.tmp, "p.json")

    def tearDown(self):
        if self._old is None:
            os.environ.pop("ROUTE_PLANNER_PROFILE", None)
        else:
            os.environ["ROUTE_PLANNER_PROFILE"] = self._old

    def test_load_missing_is_empty(self):
        self.assertEqual(profile_mod.load_profile(), {})

    def test_merge_is_deep(self):
        profile_mod.merge_profile({"terrain": "hilly", "stops": {"coffee": True}})
        profile_mod.merge_profile({"stops": {"food": True}})
        prof = profile_mod.load_profile()
        self.assertEqual(prof["terrain"], "hilly")
        self.assertEqual(prof["stops"], {"coffee": True, "food": True})

    def test_clear(self):
        profile_mod.merge_profile({"x": 1})
        profile_mod.save_profile({})
        self.assertEqual(profile_mod.load_profile(), {})

    def test_parse_value_types(self):
        self.assertEqual(profile_mod._parse_value("scenery", "coast, woodland"),
                         ["coast", "woodland"])
        self.assertIs(profile_mod._parse_value("x", "true"), True)
        self.assertEqual(profile_mod._parse_value("x", "42"), 42)
        self.assertEqual(profile_mod._parse_value("x", "3.5"), 3.5)
        self.assertEqual(profile_mod._parse_value("x", "hilly"), "hilly")


class TestGeo(unittest.TestCase):
    def test_haversine(self):
        self.assertAlmostEqual(geo.haversine_km(0, 0, 0, 1), 111.19, delta=0.5)

    def test_path_length(self):
        coords = [(0, 0), (0, 1), (0, 2)]
        self.assertAlmostEqual(geo.path_length_km(coords),
                               2 * geo.haversine_km(0, 0, 0, 1), places=6)


class TestWaterRoute(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "w.gpx")

    def test_densify_adds_points_and_keeps_ends(self):
        pts = [(50.80, -0.40), (50.76, -0.37)]
        dense = water_route.densify(pts, step_km=0.25)
        self.assertGreater(len(dense), len(pts))
        self.assertEqual(dense[0], pts[0])
        self.assertAlmostEqual(dense[-1][0], pts[-1][0], places=6)

    def test_out_and_back_returns_to_launch(self):
        pts = [(50.80, -0.40), (50.76, -0.37)]
        water_route.plan(pts, self.out, out_and_back=True, activity="paddleboard")
        dom = minidom.parse(self.out)
        trkpts = dom.getElementsByTagName("trkpt")
        first = (round(float(trkpts[0].getAttribute("lat")), 4),
                 round(float(trkpts[0].getAttribute("lon")), 4))
        last = (round(float(trkpts[-1].getAttribute("lat")), 4),
                round(float(trkpts[-1].getAttribute("lon")), 4))
        self.assertEqual(first, last)  # came back to launch

    def test_parse_points_needs_two(self):
        with self.assertRaises(ValueError):
            water_route.parse_points("50.80,-0.40")


class TestOptimizeStops(unittest.TestCase):
    def test_parse_stops(self):
        stops = optimize_stops.parse_stops("51.5,-0.1,Cafe A; 51.6,-0.2")
        self.assertEqual(stops[0]["name"], "Cafe A")
        self.assertEqual(stops[1]["name"], "Stop 2")
        self.assertEqual(stops[0]["lat"], 51.5)

    def test_parse_stops_needs_two(self):
        with self.assertRaises(ValueError):
            optimize_stops.parse_stops("51.5,-0.1,Only")

    def test_start_and_end_pinned(self):
        stops = optimize_stops.parse_stops(
            "0,0,A; 0,1,B; 0,2,C; 0,3,D")
        res = optimize_stops.optimize(stops, start_index=0, end_index=3)
        self.assertEqual(res["order"][0], "A")
        self.assertEqual(res["order"][-1], "D")

    def test_round_trip_points_close_loop(self):
        stops = optimize_stops.parse_stops("0,0,A; 0,1,B; 1,0,C")
        res = optimize_stops.optimize(stops, round_trip=True)
        first = f"{stops[0]['lat']},{stops[0]['lon']}"
        self.assertTrue(res["points"].strip().endswith(first))

    def test_points_string_feeds_route_parser(self):
        # The emitted points string must parse back via route.parse_points.
        stops = optimize_stops.parse_stops("51.5,-0.1,A; 51.6,-0.2,B; 51.7,-0.3,C")
        res = optimize_stops.optimize(stops)
        parsed = route.parse_points(res["points"])
        self.assertEqual(len(parsed), 3)

    def test_exact_matches_brute_force(self):
        random.seed(11)
        for round_trip in (False, True):
            for _ in range(30):
                stops = [{"lat": random.uniform(-1, 1), "lon": random.uniform(-1, 1),
                          "name": str(i)} for i in range(7)]
                dist = optimize_stops.build_matrix(stops)
                best = min(optimize_stops.route_length([0] + list(p), dist, round_trip)
                           for p in itertools.permutations(range(1, 7)))
                got = optimize_stops.optimize(stops, start_index=0, round_trip=round_trip)
                self.assertLessEqual(got["total_km"], best + 1e-3)


if __name__ == "__main__":
    unittest.main()
