"""J2 propagation and continuous rectangular-field crossing search for TRACE."""
import numpy as np

MU = 398600.4418
J2 = 1.08262668e-3
J2_RADIUS_KM = 6378.137


def acceleration_j2(position):
    r2=np.sum(position*position,axis=-1)
    r=np.sqrt(r2);z2=position[...,2]**2/r2
    factor=1.5*J2*(J2_RADIUS_KM/r)**2
    multiplier=np.stack((1+factor*(1-5*z2),1+factor*(1-5*z2),1+factor*(3-5*z2)),axis=-1)
    return -MU*position/(r2*r)[...,None]*multiplier


def rk4_j2(position,velocity,dt):
    a1=acceleration_j2(position)
    v2=velocity+a1*dt/2;a2=acceleration_j2(position+velocity*dt/2)
    v3=velocity+a2*dt/2;a3=acceleration_j2(position+v2*dt/2)
    v4=velocity+a3*dt;a4=acceleration_j2(position+v3*dt)
    return (position+dt/6*(velocity+2*v2+2*v3+v4),
            velocity+dt/6*(a1+2*a2+2*a3+a4))


def camera_axes_and_rate(position,velocity):
    """Radial, along-track, normal camera; derivative includes plane motion."""
    r=np.linalg.norm(position,axis=-1,keepdims=True);radial=position/r
    angular=np.cross(position,velocity);h=np.linalg.norm(angular,axis=-1,keepdims=True)
    normal=angular/h;along=np.cross(normal,radial)
    radial_dot=(velocity-radial*np.sum(radial*velocity,axis=-1,keepdims=True))/r
    hdot=np.cross(position,acceleration_j2(position))
    normal_dot=(hdot-normal*np.sum(normal*hdot,axis=-1,keepdims=True))/h
    along_dot=np.cross(normal_dot,radial)+np.cross(normal,radial_dot)
    return np.stack((radial,along,normal),axis=-1),np.stack((radial_dot,along_dot,normal_dot),axis=-1)


def camera_coordinates(position,velocity,observer_position,observer_velocity):
    axes,rate=camera_axes_and_rate(observer_position,observer_velocity)
    delta=position-observer_position
    return delta@axes,(velocity-observer_velocity)@axes+delta@rate


def hermite_coefficients(y0,dy0,y1,dy1,dt):
    """Ascending coefficients of cubic in normalized time s in [0,1]."""
    return np.stack((y0,dt*dy0,3*(y1-y0)-dt*(2*dy0+dy1),
                     2*(y0-y1)+dt*(dy0+dy1)),axis=-1)


def hermite_state(r0,v0,r1,v1,dt,s):
    s=np.asarray(s)[...,None]
    c=hermite_coefficients(r0,v0,r1,v1,dt)
    position=((c[...,3]*s+c[...,2])*s+c[...,1])*s+c[...,0]
    velocity=(3*c[...,3]*s*s+2*c[...,2]*s+c[...,1])/dt
    return position,velocity


def field_candidate_indices(y0,dy0,y1,dy1,dt,half_widths):
    """Conservative convex-hull bound for the cubic camera-coordinate model.

    A short crossing can be a candidate even when both endpoints are outside.
    """
    control=np.stack((y0,y0+dy0*dt/3,y1-dy1*dt/3,y1),axis=1)
    mask=np.max(control[:,:,0],axis=1)>0
    for axis,width in enumerate(half_widths,1):
        for sign in (-1,1):
            mask &= np.max(width*control[:,:,0]+sign*control[:,:,axis],axis=1)>=0
    return np.flatnonzero(mask)


def field_intervals(coefficients,half_widths):
    """All open-field intervals of a cubic camera trajectory in [0,1]."""
    gates=[coefficients[0]]
    for axis,width in enumerate(half_widths,1):
        gates.extend((width*coefficients[0]-coefficients[axis],width*coefficients[0]+coefficients[axis]))
    roots=[0.,1.]
    for gate in gates:
        # Near-linear/constant polynomials must not turn into unstable cubics.
        scale=max(np.max(np.abs(gate)),1.)
        polynomial=np.polynomial.polynomial.polytrim(gate,tol=scale*1e-13)
        if len(polynomial)>1:
            for value in np.polynomial.polynomial.polyroots(polynomial):
                if abs(value.imag)<1e-9 and 0<value.real<1:roots.append(float(value.real))
    roots=np.unique(np.round(roots,13));intervals=[]
    for lo,hi in zip(roots[:-1],roots[1:]):
        mid=(lo+hi)/2
        if all(np.polynomial.polynomial.polyval(mid,gate)>0 for gate in gates):
            if intervals and abs(intervals[-1][1]-lo)<1e-10:intervals[-1][1]=hi
            else:intervals.append([float(lo),float(hi)])
    return intervals


def solar_directions(elapsed_s,days_since_j2000):
    days=days_since_j2000+np.asarray(elapsed_s)/86400
    mean=np.radians((280.460+.9856474*days)%360)
    anomaly=np.radians((357.528+.9856003*days)%360)
    longitude=mean+np.radians(1.915)*np.sin(anomaly)+np.radians(.020)*np.sin(2*anomaly)
    obliquity=np.radians(23.439-.0000004*days)
    return np.stack((np.cos(longitude),np.cos(obliquity)*np.sin(longitude),np.sin(obliquity)*np.sin(longitude)),axis=-1)
