import math
import unittest

from space_debris_detection.optics import collecting_area, diffraction_limit
from space_debris_detection.radiometry import signal_electrons, signal_to_noise


class ModelTests(unittest.TestCase):
    def test_circular_aperture(self):
        self.assertAlmostEqual(collecting_area(2), math.pi)
        self.assertAlmostEqual(diffraction_limit(500e-9, 1), 610e-9)

    def test_one_joule_at_one_metre_wavelength(self):
        # Área de 1 m², exposición de 1 s y eficiencias unitarias.
        expected = 1 / (6.62607015e-34 * 299792458.0)
        actual = signal_electrons(1, 2 / math.sqrt(math.pi), 1, 1, 1, 1)
        self.assertAlmostEqual(actual / expected, 1)

    def test_shot_noise_limit(self):
        self.assertEqual(signal_to_noise(100, 0, 0, 1), 10)
        self.assertEqual(signal_to_noise(0, 0, 0, 1), 0)

    def test_noise_variance(self):
        self.assertAlmostEqual(signal_to_noise(100, 25, 5, 3), 100 / math.sqrt(200))

    def test_invalid_parameters(self):
        for diameter in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                collecting_area(diameter)
        with self.assertRaises(ValueError):
            signal_electrons(1, 1, 1, 1, 1.1, 1)
        with self.assertRaises(ValueError):
            signal_to_noise(1, 0, 0, 1.5)
