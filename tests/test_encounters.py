import unittest
import numpy as np
from space_debris_detection.encounters import (MU,J2,J2_RADIUS_KM,acceleration_j2,rk4_j2,
    hermite_coefficients,hermite_state,field_intervals,field_candidate_indices,camera_axes_and_rate)
from space_debris_detection.orbits import elements_to_states


class EncounterTests(unittest.TestCase):
    def test_fast_crossing_between_outside_endpoints(self):
        y0=np.array([[1000.,-200.,0.]])
        y1=np.array([[1000.,200.,0.]])
        d=np.array([[0.,40.,0.]])
        indices=field_candidate_indices(y0,d,y1,d,10.,[.1,.1])
        np.testing.assert_array_equal(indices,[0])
        c=hermite_coefficients(y0[0],d[0],y1[0],d[0],10.)
        np.testing.assert_allclose(field_intervals(c,[.1,.1]),[[.25,.75]],atol=1e-12)

    def test_multiple_entries_and_rear_hemisphere(self):
        # y(s)=800(s-.5)^2-150, X=1000: two intervals through |y|<100.
        c=np.array([[1000.,0.,0.,0.],[50.,-800.,800.,0.],[0.,0.,0.,0.]])
        intervals=field_intervals(c,[.1,.1])
        self.assertEqual(len(intervals),2)
        for lo,hi in intervals:
            value=np.polynomial.polynomial.polyval((lo+hi)/2,c[1])
            self.assertLess(abs(value),100)
        c[0,0]=-1000
        self.assertEqual(field_intervals(c,[.1,.1]),[])

    def test_hermite_matches_states_and_derivatives_at_endpoints(self):
        r0=np.array([7000.,2.,3.]);v0=np.array([.2,7.,.3])
        r1=np.array([6999.,72.,6.]);v1=np.array([-.3,6.9,.3])
        for s,r,v in [(0.,r0,v0),(1.,r1,v1)]:
            pr,pv=hermite_state(r0,v0,r1,v1,10.,s)
            np.testing.assert_allclose(pr,r,atol=1e-10)
            np.testing.assert_allclose(pv,v,atol=1e-10)

    def test_j2_acceleration_matches_potential_gradient(self):
        r=np.array([6800.,1200.,2000.])
        def potential(position):
            radius=np.linalg.norm(position)
            return -MU/radius*(1-J2*(J2_RADIUS_KM/radius)**2*.5*(3*(position[2]/radius)**2-1))
        numeric=[]
        for j in range(3):
            dx=np.zeros(3);dx[j]=.01
            numeric.append(-(potential(r+dx)-potential(r-dx))/.02)
        np.testing.assert_allclose(acceleration_j2(r),numeric,rtol=1e-8)

    def test_j2_one_day_step_convergence_and_energy(self):
        r,v=elements_to_states(6821.,0.,97.18768658,130.13259849,0.,0.)
        def integrate(step):
            pr,pv=r.copy(),v.copy()
            for _ in range(round(86400/step)):pr,pv=rk4_j2(pr,pv,step)
            return pr,pv
        coarse,coarse_v=integrate(20.)
        fine,fine_v=integrate(10.)
        self.assertLess(np.linalg.norm(coarse-fine),.025)  # <25 m in one day
        def energy(pr,pv):
            rr=np.linalg.norm(pr)
            return np.dot(pv,pv)/2-MU/rr*(1-J2*(J2_RADIUS_KM/rr)**2*.5*(3*(pr[2]/rr)**2-1))
        self.assertLess(abs(energy(coarse,coarse_v)/energy(r,v)-1),1e-7)
        def node(pr,pv):
            h=np.cross(pr,pv);n=np.cross([0.,0.,1.],h)
            return np.degrees(np.arctan2(n[1],n[0]))%360
        precession=(node(coarse,coarse_v)-node(r,v)+180)%360-180
        self.assertTrue(.9<precession<1.1)

    def test_camera_derivative_includes_j2_plane_motion(self):
        r,v=elements_to_states(6821.,.001,97.,130.,0.,50.)
        axes,derivative=camera_axes_and_rate(r,v)
        np.testing.assert_allclose(axes.T@axes,np.eye(3),atol=1e-14)
        dt=.001
        r1,v1=rk4_j2(r,v,dt);a1,_=camera_axes_and_rate(r1,v1)
        r0,v0=rk4_j2(r,v,-dt);a0,_=camera_axes_and_rate(r0,v0)
        np.testing.assert_allclose(derivative,(a1-a0)/(2*dt),atol=1e-11)
