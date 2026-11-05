import unittest

import numpy as np

from space_debris_detection.orbits import elements_to_states
from space_debris_detection.sensitivity import SCENARIOS, make_scenario, audit_scenario, eccentricity_limit


class SensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        n = 5000
        rng = np.random.default_rng(91)
        a = 6371+rng.uniform(250, 1950, n)
        cls.nominal = {
            "object_id": np.array([f"TEST-{j}" for j in range(n)]),
            "diameter_m": rng.uniform(.01, .2, n), "altitude_km": a-6371,
            "semi_major_axis_km": a, "inclination_deg": rng.uniform(20, 120, n),
            "eccentricity": eccentricity_limit(a)*rng.uniform(.1, .9, n),
            "raan_deg": rng.uniform(0, 360, n), "argument_of_perigee_deg": rng.uniform(0, 360, n),
            "mean_anomaly_deg": rng.uniform(0, 360, n), "epoch_utc": np.full(n, "2026-11-05T00:00:00Z"),
            "frame": np.full(n, "TEME"), "statistical_weight": np.full(n, 7.)}

    def test_nine_alternatives_preserve_controls_and_nominal(self):
        before = {key: value.copy() for key, value in self.nominal.items()}
        self.assertEqual(len(SCENARIOS), 9)
        for name in SCENARIOS:
            with self.subTest(name=name):
                result = make_scenario(self.nominal, name)
                audit = audit_scenario(self.nominal, result, name)
                self.assertEqual(audit["status"], "passed")
                for key in self.nominal:
                    np.testing.assert_array_equal(self.nominal[key], before[key])

    def test_eccentricity_order_and_feasible_support(self):
        low = make_scenario(self.nominal, "eccentricity_low")["eccentricity"]
        high = make_scenario(self.nominal, "eccentricity_high")["eccentricity"]
        self.assertTrue((low < self.nominal["eccentricity"]).all())
        self.assertTrue((high > self.nominal["eccentricity"]).all())
        self.assertTrue((high < eccentricity_limit(self.nominal["semi_major_axis_km"])).all())

    def test_circular_latitude_uniform_and_gauge_independent(self):
        result = make_scenario(self.nominal, "eccentricity_circular")
        sorted_u = np.sort(result["argument_of_latitude_deg"])/360
        n = len(sorted_u)
        ks = max(np.max(np.arange(1, n+1)/n-sorted_u), np.max(sorted_u-np.arange(n)/n))
        self.assertLess(ks, .03)
        # Changing the circular gauge omega and compensating M leaves state fixed.
        r, v = elements_to_states(result["semi_major_axis_km"], result["eccentricity"],
            result["inclination_deg"], result["raan_deg"], np.zeros(n), result["argument_of_latitude_deg"])
        np.testing.assert_allclose(r, np.column_stack([result[f"{k}_km"] for k in "xyz"]), atol=1e-9)
        np.testing.assert_allclose(v, np.column_stack([result[f"v{k}_km_s"] for k in "xyz"]), atol=1e-12)

    def test_equally_spaced_angle_models_and_repeatability(self):
        for key, prefix in (("raan_deg", "raan"), ("argument_of_perigee_deg", "argp")):
            for points in (12, 8, 4):
                name = f"{prefix}_{points}_{'planes' if prefix == 'raan' else 'positions'}"
                data = make_scenario(self.nominal, name)
                repeated = make_scenario(self.nominal, name)
                np.testing.assert_array_equal(data[key], repeated[key])
                angles, counts = np.unique(data[key], return_counts=True)
                np.testing.assert_array_equal(angles, np.arange(points)*(360/points))
                self.assertLessEqual(counts.max()-counts.min(), 1)
                self.assertEqual(int(counts.sum()), len(self.nominal["object_id"]))
            eight = make_scenario(self.nominal, f"{prefix}_8_{'planes' if prefix == 'raan' else 'positions'}")[key]
            four = make_scenario(self.nominal, f"{prefix}_4_{'planes' if prefix == 'raan' else 'positions'}")[key]
            np.testing.assert_array_equal(np.floor(eight/90)*90, four)
