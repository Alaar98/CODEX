from pathlib import Path
import unittest

import numpy as np
from space_debris_detection.optical_validation import load_baseline, OpticalModel, StudyCase
from space_debris_detection.snapshot import earth_clear, sunlit_cylindrical, field_overlap, classify_snapshot


class SnapshotTests(unittest.TestCase):
    def test_occultation_and_shadow_are_separate(self):
        observer=np.array([6821.,0,0])
        positions=np.array([[7171.,0,0],[-7171.,0,0],[0,7171.,0]])
        np.testing.assert_array_equal(earth_clear(observer,positions),[True,False,False])
        np.testing.assert_array_equal(sunlit_cylindrical(positions,np.array([1.,0,0])),[True,False,True])

    def test_partial_exposure_at_field_edge(self):
        coordinates=np.array([[0.,0],[1.,0],[2.,0],[2.,0]])
        rates=np.array([[0.,0],[1.,0],[1.,0],[0.,0]])
        np.testing.assert_allclose(field_overlap(coordinates,rates,[1.,1.],.1),[.1,.05,0,0])

    def test_snapshot_detects_lit_in_field_and_rejects_shadow(self):
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        model=OpticalModel(b);case=StudyCase(.08,14,60,.2,5000)
        pop={'x_km':np.array([6921.,6921.]),'y_km':np.array([0.,1000.]),'z_km':np.zeros(2),
             'vx_km_s':np.zeros(2),'vy_km_s':np.zeros(2),'vz_km_s':np.zeros(2),
             'diameter_m':np.ones(2)}
        sun=np.array([-.2,np.sqrt(.96),0.])
        good=classify_snapshot(pop,model,case,sun)
        np.testing.assert_array_equal(good['in_fov'],[True,False])
        np.testing.assert_array_equal(good['detectable'],[True,False])
        self.assertGreater(good['snr'][0],5)
        shadow=classify_snapshot(pop,model,case,np.array([-1.,0,0]))
        self.assertFalse(shadow['sunlit'][0])
        self.assertFalse(shadow['detectable'][0])
        self.assertEqual(shadow['snr'][0],0)

    def test_explicit_overlap_scales_signal_and_keeps_exposure_background(self):
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        m=OpticalModel(b);c=StudyCase(.08,14,60,.2,5000)
        full=m.evaluate(c,100000,diameter_m=.1,apparent_rate_rad_s=0)
        half=m.evaluate(c,100000,diameter_m=.1,apparent_rate_rad_s=0,exposure_overlap_s=b['t_int']/2)
        self.assertAlmostEqual(float(half['signal_e']/full['signal_e']),.5)
        self.assertEqual(half['pixels'],full['pixels'])
        self.assertTrue(half['partial_transit'])
        zero=m.evaluate(c,100000,diameter_m=.1,exposure_overlap_s=0)
        self.assertFalse(zero['eligible'])
        self.assertEqual(zero['snr'],0)
