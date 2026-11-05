from pathlib import Path
import unittest
import numpy as np

from space_debris_detection.population import generate_population, load_models

REFERENCE = Path(__file__).resolve().parents[1] / "data/reference"


class PopulationTests(unittest.TestCase):
    def test_bounds_orbits_and_reproducibility(self):
        data, meta = generate_population(REFERENCE)
        again, _ = generate_population(REFERENCE)
        self.assertEqual(meta["count"], 50000)
        for key, values in data.items():
            self.assertEqual(len(values), 50000)
            self.assertTrue(np.isfinite(values).all())
            np.testing.assert_array_equal(values, again[key])
        self.assertTrue(((data["altitude_km"] >= 200) & (data["altitude_km"] <= 2000)).all())
        self.assertTrue((data["diameter_m"] >= .01).all())
        self.assertTrue((data["diameter_m"] <= meta["max_size_cutoff_m"]).all())
        np.testing.assert_allclose(data["semi_major_axis_km"] - data["altitude_km"], 6371)
        self.assertTrue((data["eccentricity"] == 0).all())

    def test_size_class_and_altitude_distributions(self):
        data, meta = generate_population(REFERENCE)
        large = data["diameter_m"] >= .1
        p = meta["probability_gt_10_cm"]
        self.assertLess(abs(large.mean() - p), 5 * np.sqrt(p * (1-p) / len(large)))
        _, _, h, weights = load_models(REFERENCE)
        # Contraste de CDF empírica con el perfil integrado en cada clase.
        for group in (0, 1):
            w = weights[group]
            cdf = np.r_[0, np.cumsum((w[1:] + w[:-1]) / 2 * np.diff(h))]
            cdf /= cdf[-1]
            samples = data["altitude_km"][large == bool(group)]
            for threshold in (500, 800, 1200, 1600):
                expected = np.interp(threshold, h, cdf)
                tolerance = 5 * np.sqrt(expected * (1-expected) / len(samples)) + .002
                self.assertLess(abs((samples <= threshold).mean() - expected), tolerance)

    def test_size_cumulative_shape(self):
        data, _ = generate_population(REFERENCE)
        d, n, _, _ = load_models(REFERENCE)
        for lower, upper, threshold in ((.01, .1, .03), (.1, float(d[-1]), .3)):
            selected = data["diameter_m"][(data["diameter_m"] >= lower) & (data["diameter_m"] < upper)]
            # N(d) de la figura determina la fracción bajo el umbral en la clase.
            counts = 10 ** np.interp(np.log10([lower, threshold, upper]), np.log10(d), np.log10(n))
            expected = (counts[0] - counts[1]) / (counts[0] - counts[2])
            self.assertLess(abs((selected < threshold).mean() - expected),
                            5 * np.sqrt(expected * (1-expected) / len(selected)) + .002)
