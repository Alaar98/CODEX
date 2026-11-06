from pathlib import Path
import unittest
import numpy as np

from scripts.plot_snr_range_maps import limiting_magnitude
from space_debris_detection.optical_validation import OpticalModel, StudyCase, load_baseline


class LimitingMagnitudeTests(unittest.TestCase):
    def test_boundary_separates_detectable_and_fainter_sources(self):
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        model=OpticalModel(b);case=StudyCase(.08,14,60,.2,5000)
        ranges=np.array([10.,500.,1000.,100000.,5000000.,20000000.])
        limit=limiting_magnitude(model,case,ranges)
        at=model.evaluate(case,ranges,magnitude_ab=limit)
        brighter=model.evaluate(case,ranges,magnitude_ab=limit-.1)
        fainter=model.evaluate(case,ranges,magnitude_ab=limit+.1)
        np.testing.assert_allclose(at['snr'],5,rtol=1e-12)
        self.assertTrue(np.all(brighter['snr']>5))
        self.assertTrue(np.all(fainter['snr']<5))
        self.assertTrue(at['partial_transit'][0])
        self.assertFalse(at['partial_transit'][-1])
