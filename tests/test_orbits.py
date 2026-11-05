import unittest

import numpy as np

from space_debris_detection.orbits import MU_KM3_S2, elements_to_states, state_to_elements


class OrbitConversionTests(unittest.TestCase):
    def test_circular_reference_state(self):
        r, v = elements_to_states(7000, 0, 0, 0, 0, 0)
        np.testing.assert_allclose(r, [7000, 0, 0], atol=1e-10)
        np.testing.assert_allclose(v, [0, np.sqrt(MU_KM3_S2/7000), 0], atol=1e-10)

    def test_eccentric_apogee_and_energy(self):
        r, v = elements_to_states(7500, .1, 0, 0, 0, 180)
        np.testing.assert_allclose(r, [-8250, 0, 0], atol=1e-10)
        self.assertAlmostEqual(np.dot(v, v)/2-MU_KM3_S2/np.linalg.norm(r), -MU_KM3_S2/(2*7500))

    def test_inclined_elliptic_round_trip(self):
        initial = [7300, .04, 98, 359, 270, 43]
        r, v = elements_to_states(*initial)
        result = state_to_elements(r, v)
        for key, expected in zip(("semi_major_axis_km", "eccentricity", "inclination_deg", "raan_deg",
                                  "argument_of_perigee_deg", "mean_anomaly_deg"), initial):
            self.assertAlmostEqual(result[key], expected, places=8)
