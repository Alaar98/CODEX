from dataclasses import replace
from pathlib import Path
import unittest

import numpy as np

from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline, paper_reference, peak_pixel_fraction


class OpticalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = load_baseline(next((Path(__file__).resolve().parents[1]/"docs/references").glob("*.xlsx")))
        cls.model = OpticalModel(cls.b)
        cls.case = StudyCase((cls.b["D_ap_min"]+cls.b["D_ap_max"])/2,
                            (cls.b["FOV_min"]+cls.b["FOV_max"])/2, 60, cls.b["albedo_nom"], 5000)

    def test_lambert_and_flux_scalings(self):
        m, c = self.model, self.case
        self.assertAlmostEqual(float(m.phase_function(0)), 1)
        self.assertAlmostEqual(float(m.phase_function(90)), 1/np.pi)
        self.assertAlmostEqual(float(m.phase_function(180)), 0)
        self.assertAlmostEqual(float(m.phase_function(135)), .0483023837, places=8)
        s = m.evaluate(c, 100000, diameter_m=.1)["signal_e"]
        self.assertAlmostEqual(m.evaluate(c, 200000, diameter_m=.1)["signal_e"]/s, .25)
        self.assertAlmostEqual(m.evaluate(c, 100000, diameter_m=.2)["signal_e"]/s, 4)
        result = m.evaluate(c, 100000, diameter_m=.1)
        equivalent = m.evaluate(c, 100000, magnitude_ab=result["magnitude_ab"])
        self.assertAlmostEqual(float(result["snr"]), float(equivalent["snr"]))

    def test_noise_motion_and_domains(self):
        m, c = self.model, self.case
        low = m.evaluate(c, 100000, diameter_m=.1)
        self.assertLess(m.evaluate(replace(c, transverse_speed_m_s=15000),100000,diameter_m=.1)["snr"],low["snr"])
        zero = m.evaluate(replace(c, transverse_speed_m_s=c.frame_rate_rad_s*100000),100000,diameter_m=.1)
        self.assertGreater(float(zero["pixels"]), 1)
        self.assertLess(float(zero["streak_px"]), 1e-10)
        self.assertFalse(m.evaluate(replace(c,phase_deg=135),100000,diameter_m=.1)["eligible"])
        minimum = m.transit_lower_range(c)
        self.assertFalse(m.evaluate(c, minimum*.99,diameter_m=.01)["full_transit"])
        self.assertTrue(m.evaluate(c, minimum*1.01,diameter_m=.01)["full_transit"])

    def test_range_scan_convergence_and_boundary(self):
        boundaries = []
        for points in (1025,2049):
            iv = self.model.range_intervals(self.case,.1,np.geomspace(100,2e7,points))
            self.assertTrue(iv)
            boundaries.append(iv[-1]["upper_m"])
            self.assertFalse(iv[-1]["upper_censored"])
            snr = self.model.evaluate(self.case,iv[-1]["upper_m"],diameter_m=.1)["snr"]
            self.assertAlmostEqual(float(snr),self.b["SNR_min"],places=5)
        self.assertLess(abs(boundaries[0]/boundaries[1]-1),1e-5)

    def test_paper_power_and_noise_reference(self):
        result = paper_reference(extraction_pixels=10)
        # Independently evaluate Eq.1–7 with the stated camera power.
        power = .4*.3*1361*.1**2*(.4/2.8)**2/(8*100000**2)
        signal = .61*power*.025/(6.62607015e-34*600e12)
        self.assertAlmostEqual(result["signal_e"], signal)
        expected = signal/np.sqrt(signal+10*(.001+4.3**2))
        self.assertAlmostEqual(result["snr_with_specified_pixels"],expected)
        self.assertGreater(result["eq9_literal_value_per_m"],1e6)

    def test_peak_pixel_psf_and_streak_integral(self):
        import math
        sigma = .85
        point_axis = math.erf(.5/(np.sqrt(2)*sigma))
        self.assertAlmostEqual(float(peak_pixel_fraction(0,sigma)),point_axis**2)
        self.assertAlmostEqual(float(peak_pixel_fraction(100,sigma)),point_axis/100)
        for length in (.1, 1., 5.):
            offsets = np.linspace(-length/2,length/2,20001)
            along = np.array([.5*(math.erf((.5-u)/(np.sqrt(2)*sigma))-math.erf((-.5-u)/(np.sqrt(2)*sigma))) for u in offsets])
            numerical = np.trapezoid(along,offsets)/length*point_axis
            self.assertAlmostEqual(float(peak_pixel_fraction(length,sigma)),numerical,places=8)

    def test_full_well_saturation_is_per_pixel(self):
        self.assertEqual(self.b['FWC_high_gain'],15000)
        self.assertEqual(self.b['FWC_low_gain_lower_bound'],140000)
        near = self.model.evaluate(self.case,100000.,diameter_m=10.)
        far = self.model.evaluate(self.case,2e7,diameter_m=10.)
        self.assertGreater(float(near['peak_pixel_e']),15000)
        self.assertFalse(bool(near['unsaturated']))
        self.assertFalse(bool(near['eligible']))
        self.assertTrue(bool(far['unsaturated']))
