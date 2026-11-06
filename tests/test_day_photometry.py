import unittest
import numpy as np
from pathlib import Path
from scripts.plot_day_encounters import evaluate_nodes
from space_debris_detection.encounters import rk4_j2
from space_debris_detection.optical_validation import OpticalModel,StudyCase,load_baseline


class DayPhotometryTests(unittest.TestCase):
    def test_partial_pass_margin_matches_snr_with_actual_exposure_time(self):
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        model=OpticalModel(b);case=StudyCase(.08,14,60,.2,5000)
        ro=np.array([6821.,0,0]);vo=np.array([0.,case.frame_rate_rad_s*6821,0.])
        ro1,vo1=rk4_j2(ro,vo,.1)
        r0=ro+np.array([1.,-.7,0]);v0=vo+np.array([0.,14.,0])
        tr={'observer_t':np.array([0.,.1]),'observer_r':np.array([ro,ro1]),
            'observer_v':np.array([vo,vo1]),'piece_step':np.array([0]),
            'piece_r0':r0[None,:],'piece_v0':v0[None,:],
            'piece_r1':(r0+v0*.1)[None,:],'piece_v1':v0[None,:],
            'event_start':np.array([.0413]),'event_end':np.array([.0587]),'event_object':np.array([0])}
        result=evaluate_nodes(np.array([.05]),0,[0],tr,{'diameter_m':np.array([.05])},model,case,180.)
        self.assertTrue(result['valid'][0])
        self.assertAlmostEqual(result['visible_time_s'][0],.0174)
        self.assertLess(result['visible_time_s'][0],b['t_int'])
        self.assertLess(result['magnitude_margin'][0],0)
        self.assertGreater(result['snr'][0],5)
        # Independently substitute the limiting apparent magnitude with this
        # same rate and partial overlap: its SNR must be exactly five.
        boundary=model.evaluate(case,result['range_km']*1000,
             magnitude_ab=result['limiting_magnitude_ab'],apparent_rate_rad_s=result['angular_rate_rad_s'],
             exposure_overlap_s=result['visible_time_s'])
        np.testing.assert_allclose(boundary['snr'],5,rtol=1e-12)
