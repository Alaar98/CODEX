from pathlib import Path
import tempfile
import unittest

import numpy as np

from space_debris_detection.orbital_population import assign_orbital_elements, sample_inclinations
from space_debris_detection.population import generate_population
from space_debris_detection.plotting import population_figures

REFERENCE = Path(__file__).resolve().parents[1] / "data/reference"


class OrbitalPopulationTests(unittest.TestCase):
    def test_esa_conditioning_and_zero_cells(self):
        table = np.genfromtxt(REFERENCE / "esa2026_inclination_perigee.csv", delimiter=",", names=True)
        self.assertEqual(len(table), 574)
        h = np.repeat([600., 800., 1400.], 12000)
        inclination, fallback = sample_inclinations(REFERENCE, h, np.random.default_rng(4))
        self.assertEqual(fallback, 0)
        for altitude in (600., 800., 1400.):
            cell = table[table["perigee_min_km"] == altitude]
            actual, _ = np.histogram(inclination[h == altitude], np.arange(0, 181, 3))
            expected = np.zeros(60)
            expected[(cell["inclination_min_deg"]/3).astype(int)] = cell["approximate_count"]
            expected /= expected.sum()
            self.assertTrue((actual[expected == 0] == 0).all())
            np.testing.assert_array_less(np.abs(actual/12000-expected),
                                         5*np.sqrt(expected*(1-expected)/12000)+.001)

    def test_absent_catalogue_is_explicit_not_circular_substitution(self):
        base, _ = generate_population(REFERENCE, count=100)
        data, meta = assign_orbital_elements(base, REFERENCE)
        again, _ = assign_orbital_elements(base, REFERENCE)
        self.assertEqual(meta["missing_parameters"], ["eccentricity", "raan_deg", "argument_of_perigee_deg"])
        self.assertNotIn("eccentricity", data)
        self.assertNotIn("raan_deg", data)
        np.testing.assert_array_equal(data["inclination_deg"], again["inclination_deg"])
        self.assertTrue(((data["inclination_deg"] >= 0) & (data["inclination_deg"] < 180)).all())

    def test_empirical_tuple_bootstrap_and_physical_bounds(self):
        # Artificial fixture for algorithm testing; never used as empirical source.
        dtype = [("catalogue_id", int), ("mean_altitude_km", float), ("perigee_km", float),
                 ("apogee_km", float), ("eccentricity", float), ("raan_deg", float),
                 ("argument_of_perigee_deg", float), ("epoch_utc", "U30"),
                 ("source_epoch_utc", "U30"), ("source_family", "U20"), ("frame", "U10")]
        donors = np.array([(1, 700, 690, 710, .001, 359, 40, "2026-01-02T00:00:00Z", "2026-01-01T00:00:00", "TEST-1", "TEME"),
                           (2, 800, 780, 820, .002, 1, 220, "2026-01-02T00:00:00Z", "2026-01-02T00:00:00", "TEST-2", "TEME")], dtype=dtype)
        base = {"altitude_km": np.full(200, 750.), "diameter_m": np.full(200, .02),
                "semi_major_axis_km": np.full(200, 7121.)}
        data, meta = assign_orbital_elements(base, REFERENCE, catalogue=donors)
        self.assertFalse(meta["missing_parameters"])
        for e, raan, omega in zip(data["eccentricity"], data["raan_deg"], data["argument_of_perigee_deg"]):
            self.assertIn((e, raan, omega), {(.001, 359, 40), (.002, 1, 220)})
        self.assertTrue((data["perigee_km"] >= 200).all())
        self.assertTrue((data["apogee_km"] <= 2000).all())
        self.assertTrue(meta["common_epoch_validated"])
        self.assertTrue(((data["mean_anomaly_deg"] >= 0) & (data["mean_anomaly_deg"] < 360)).all())
        donors["epoch_utc"][0] = "2026-01-03T00:00:00Z"
        with self.assertRaises(ValueError):
            assign_orbital_elements(base, REFERENCE, catalogue=donors)

    def test_publication_maps_count_all_objects(self):
        base, _ = generate_population(REFERENCE, count=300)
        data, _ = assign_orbital_elements(base, REFERENCE)
        with tempfile.TemporaryDirectory() as directory:
            manifest = population_figures(data, Path(directory))
            self.assertEqual(manifest["altitude_histogram_objects_counted"], 300)
            self.assertEqual(set(manifest["unavailable"]), {"raan_deg", "argument_of_perigee_deg", "eccentricity", "mean_anomaly_deg"})
            for mapping in manifest["maps"].values():
                self.assertEqual(mapping["objects_counted"], 300)
            for name in ("trace_nominal_size_vs_altitude", "trace_nominal_inclination_vs_altitude", "trace_nominal_altitude_histogram"):
                self.assertGreater((Path(directory) / f"{name}.png").stat().st_size, 1000)
            self.assertTrue(all(p.suffix == ".png" for p in Path(directory).iterdir()))
