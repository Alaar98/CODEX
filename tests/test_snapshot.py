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

    def test_rotating_observer_and_camera_preserve_geometry(self):
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        m=OpticalModel(b);c=StudyCase(.08,14,60,.2,5000)
        pop={'x_km':np.array([6921.,6921.]),'y_km':np.array([0.,1000.]),'z_km':np.zeros(2),
             'vx_km_s':np.zeros(2),'vy_km_s':np.zeros(2),'vz_km_s':np.zeros(2),'diameter_m':np.ones(2)}
        sun=np.array([-.2,np.sqrt(.96),0.])
        reference=classify_snapshot(pop,m,c,sun)
        angle=1.3
        rotate=np.array([[np.cos(angle),-np.sin(angle),0],[np.sin(angle),np.cos(angle),0],[0,0,1]])
        rotated=dict(pop)
        for names in [('x_km','y_km','z_km'),('vx_km_s','vy_km_s','vz_km_s')]:
            values=np.column_stack([pop[k] for k in names])@rotate.T
            for j,name in enumerate(names):rotated[name]=values[:,j]
        result=classify_snapshot(rotated,m,c,rotate@sun,elapsed_s=angle/c.frame_rate_rad_s)
        for field in ('in_fov','visible','detectable','sunlit','earth_clear'):
            np.testing.assert_array_equal(result[field],reference[field])
        np.testing.assert_allclose(result['snr'],reference['snr'],atol=1e-10)
        self.assertAlmostEqual(np.linalg.norm(result['observer_position_km']),6821.)

    def test_two_body_propagation_returns_after_period_without_mutation(self):
        from space_debris_detection.snapshot import propagate_population
        from space_debris_detection.orbits import MU_KM3_S2
        pop={'semi_major_axis_km':np.array([7000.]),'eccentricity':np.array([.02]),
             'inclination_deg':np.array([60.]),'raan_deg':np.array([30.]),
             'argument_of_perigee_deg':np.array([20.]),'mean_anomaly_deg':np.array([10.])}
        initial=propagate_population(pop,0.)
        period=2*np.pi*np.sqrt(7000.**3/MU_KM3_S2)
        final=propagate_population(pop,period)
        for field in ('x_km','y_km','z_km','vx_km_s','vy_km_s','vz_km_s'):
            np.testing.assert_allclose(final[field],initial[field],atol=1e-9)
        self.assertNotIn('x_km',pop)
        self.assertEqual(pop['mean_anomaly_deg'][0],10.)

    def test_inclined_observer_state_and_camera(self):
        from space_debris_detection.orbits import elements_to_states
        from scripts.compare_sso_observer import sso_inclination_deg
        b=load_baseline(next((Path(__file__).resolve().parents[1]/'docs/references').glob('*.xlsx')))
        m=OpticalModel(b);c=StudyCase(.08,14,60,.2,5000)
        inc=sso_inclination_deg(450.)
        self.assertTrue(96 < inc < 99)
        nodal_rate=-1.5*1.08262668e-3*c.frame_rate_rad_s*(6378.137/6821)**2*np.cos(np.radians(inc))
        self.assertAlmostEqual(nodal_rate,2*np.pi/(365.2422*86400),places=14)
        elapsed=1000.;u=15+np.degrees(c.frame_rate_rad_s*elapsed)
        r,v=elements_to_states(6821,0,inc,40,0,u)
        # Put a target directly along the observer's inclined zenith.
        radial=r/np.linalg.norm(r)
        position=r+100*radial
        pop={f'{axis}_km':np.array([position[j]]) for j,axis in enumerate('xyz')}
        pop.update({f'v{axis}_km_s':np.array([v[j]]) for j,axis in enumerate('xyz')})
        pop['diameter_m']=np.array([1.])
        result=classify_snapshot(pop,m,c,np.array([-1.,0,0]),elapsed_s=elapsed,
            observer_inclination_deg=inc,observer_raan_deg=40,observer_initial_u_deg=15)
        np.testing.assert_allclose(result['observer_position_km'],r,atol=1e-10)
        np.testing.assert_allclose(result['observer_velocity_km_s'],v,atol=1e-12)
        self.assertTrue(result['in_fov'][0])
