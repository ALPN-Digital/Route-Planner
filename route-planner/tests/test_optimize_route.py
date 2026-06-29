"""Tests for the route optimizer. Standard library only: `python3 -m unittest`."""
import itertools
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import optimize_route as o  # noqa: E402


def brute_force_length(stops, round_trip):
    dist = o.build_distance_matrix(stops)
    n = len(stops)
    return min(
        o.route_length([0] + list(p), dist, round_trip)
        for p in itertools.permutations(range(1, n))
    )


class TestHaversine(unittest.TestCase):
    def test_known_distance(self):
        # NYC to LA is ~3936 km.
        nyc = {"lat": 40.7128, "lon": -74.0060}
        la = {"lat": 34.0522, "lon": -118.2437}
        self.assertAlmostEqual(o.haversine_km(nyc, la), 3936, delta=20)

    def test_zero(self):
        p = {"lat": 1.0, "lon": 2.0}
        self.assertEqual(o.haversine_km(p, p), 0.0)


class TestOptimize(unittest.TestCase):
    def test_single_stop(self):
        res = o.optimize([{"name": "A", "lat": 0.0, "lon": 0.0}])
        self.assertEqual(res["order"], ["A"])
        self.assertEqual(res["total_km"], 0.0)

    def test_missing_coordinates_raises(self):
        with self.assertRaises(o.RouteError):
            o.optimize([{"name": "A", "address": "somewhere"}])

    def test_empty_raises(self):
        with self.assertRaises(o.RouteError):
            o.optimize([])

    def test_start_is_pinned(self):
        stops = [
            {"name": "A", "lat": 0.0, "lon": 0.0},
            {"name": "B", "lat": 0.0, "lon": 1.0},
            {"name": "C", "lat": 0.0, "lon": 2.0},
            {"name": "D", "lat": 0.0, "lon": 3.0},
        ]
        res = o.optimize(stops, start_index=2)
        self.assertEqual(res["order"][0], "C")

    def test_end_is_pinned(self):
        stops = [
            {"name": "A", "lat": 0.0, "lon": 0.0},
            {"name": "B", "lat": 0.0, "lon": 1.0},
            {"name": "C", "lat": 0.0, "lon": 2.0},
            {"name": "D", "lat": 0.0, "lon": 3.0},
        ]
        res = o.optimize(stops, start_index=0, end_index=1)
        self.assertEqual(res["order"][0], "A")
        self.assertEqual(res["order"][-1], "B")

    def test_round_trip_url_closes_loop(self):
        stops = [
            {"name": "A", "lat": 0.0, "lon": 0.0},
            {"name": "B", "lat": 0.0, "lon": 1.0},
            {"name": "C", "lat": 1.0, "lon": 0.0},
        ]
        res = o.optimize(stops, round_trip=True)
        first = f"{stops[0]['lat']},{stops[0]['lon']}"
        self.assertTrue(res["google_maps_url"].endswith(first))

    def test_matches_brute_force(self):
        random.seed(42)
        for round_trip in (False, True):
            for _ in range(50):
                stops = [
                    {"name": str(i), "lat": random.uniform(-1, 1), "lon": random.uniform(-1, 1)}
                    for i in range(7)
                ]
                res = o.optimize(stops, start_index=0, round_trip=round_trip)
                best = brute_force_length(stops, round_trip)
                # total_km is rounded to 3 decimals; allow for that rounding.
                self.assertLessEqual(res["total_km"], best + 1e-3)

    def test_deterministic(self):
        random.seed(7)
        stops = [
            {"name": str(i), "lat": random.uniform(-2, 2), "lon": random.uniform(-2, 2)}
            for i in range(12)
        ]
        a = o.optimize(stops, round_trip=True)["order"]
        b = o.optimize(stops, round_trip=True)["order"]
        self.assertEqual(a, b)


class TestParsing(unittest.TestCase):
    def test_parse_json_list(self):
        stops = o.parse_stops('[{"name":"A","lat":1,"lon":2}]', "json")
        self.assertEqual(stops[0]["name"], "A")
        self.assertEqual(stops[0]["lat"], 1.0)

    def test_parse_json_wrapped(self):
        stops = o.parse_stops('{"stops":[{"name":"A","lat":1,"lon":2}]}', "json")
        self.assertEqual(len(stops), 1)

    def test_parse_csv(self):
        stops = o.parse_stops("name,lat,lon\nA,1,2\nB,3,4\n", "csv")
        self.assertEqual(len(stops), 2)
        self.assertEqual(stops[1]["lon"], 4.0)

    def test_find_index_case_insensitive(self):
        stops = [{"name": "Warehouse"}, {"name": "Home"}]
        self.assertEqual(o._find_index(stops, "warehouse", None), 0)

    def test_find_index_missing_raises(self):
        with self.assertRaises(o.RouteError):
            o._find_index([{"name": "A"}], "Z", None)


if __name__ == "__main__":
    unittest.main()
