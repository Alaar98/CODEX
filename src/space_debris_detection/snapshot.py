"""Illustrative instantaneous visibility, with explicit observer and Sun geometry."""
from datetime import datetime, timezone

import numpy as np
from .orbits import elements_to_states, MU_KM3_S2


def approximate_sun_direction(epoch_utc):
    """Low precision geocentric solar direction, mean equator/equinox of date.

    Used as an approximate TEME direction (no nutation/equation-of-equinoxes
    correction). Not a precision solar ephemeris; use away from shadow edges.
    """
    time = datetime.fromisoformat(epoch_utc.replace('Z', '+00:00'))
    days = (time-datetime(2000,1,1,12,tzinfo=timezone.utc)).total_seconds()/86400
    mean_longitude = np.radians((280.460+.9856474*days)%360)
    anomaly = np.radians((357.528+.9856003*days)%360)
    longitude = mean_longitude+np.radians(1.915)*np.sin(anomaly)+np.radians(.020)*np.sin(2*anomaly)
    obliquity = np.radians(23.439-.0000004*days)
    return np.array([np.cos(longitude),np.cos(obliquity)*np.sin(longitude),
                     np.sin(obliquity)*np.sin(longitude)])


def earth_clear(observer, positions, radius_km=6371.):
    delta = positions-observer
    t = np.clip(-np.sum(observer*delta,axis=1)/np.sum(delta*delta,axis=1),0,1)
    return np.linalg.norm(observer+t[:,None]*delta,axis=1)>radius_km


def sunlit_cylindrical(positions, sun_direction, radius_km=6371.):
    along = positions@sun_direction
    perpendicular = np.linalg.norm(positions-along[:,None]*sun_direction,axis=1)
    return (along>=0) | (perpendicular>radius_km)


def field_overlap(coordinates, rates, half_widths, exposure_s):
    """Time within a rectangular field, linear tangent coordinates, centred read."""
    enter = np.full(len(coordinates),-exposure_s/2)
    leave = np.full(len(coordinates),exposure_s/2)
    for axis, limit in enumerate(half_widths):
        position, speed = coordinates[:,axis],rates[:,axis]
        moving = np.abs(speed)>1e-15
        safe = np.where(moving,speed,1.)
        a,b = (-limit-position)/safe,(limit-position)/safe
        enter = np.maximum(enter,np.where(moving,np.minimum(a,b),-np.inf))
        leave = np.minimum(leave,np.where(moving,np.maximum(a,b),np.inf))
        leave = np.where(~moving & (np.abs(position)>limit),-np.inf,leave)
    return np.maximum(0,leave-enter)


def propagate_population(population, elapsed_s):
    """Two-body propagation in the fixed TEME axes of the nominal epoch.

    No J2, drag or rotation of the reference axes; intended for a short scan.
    Original population arrays remain untouched.
    """
    mean = population['mean_anomaly_deg'] + np.degrees(
        np.sqrt(MU_KM3_S2/population['semi_major_axis_km']**3)*elapsed_s)
    position, velocity = elements_to_states(population['semi_major_axis_km'],
        population['eccentricity'],population['inclination_deg'],population['raan_deg'],
        population['argument_of_perigee_deg'],mean)
    result = dict(population)
    for j,axis in enumerate('xyz'):
        result[f'{axis}_km'] = position[:,j]
        result[f'v{axis}_km_s'] = velocity[:,j]
    return result


def classify_snapshot(population, model, case, sun_direction, *, elapsed_s=0., geometry_only=False):
    """450 km reference extended to a circular prograde equatorial orbit.

    Camera zenith, horizontal along-track, vertical orbit normal; exposure
    centred on the propagated epoch. Sun at infinity; spherical opaque Earth.
    """
    angle = case.frame_rate_rad_s*elapsed_s
    radial = np.array([np.cos(angle),np.sin(angle),0.])
    along_track = np.array([-np.sin(angle),np.cos(angle),0.])
    camera_axes = np.column_stack((radial,along_track,[0.,0.,1.]))
    observer = (6371+case.observer_altitude_km)*radial
    velocity = case.frame_rate_rad_s*(6371+case.observer_altitude_km)*along_track
    position = np.column_stack([population[k] for k in ('x_km','y_km','z_km')])
    target_velocity = np.column_stack([population[k] for k in ('vx_km_s','vy_km_s','vz_km_s')])
    delta = position-observer
    ranges = np.linalg.norm(delta,axis=1)
    los = delta/ranges[:,None]
    relative_velocity = target_velocity-velocity
    frame_omega = np.array([0.,0.,case.frame_rate_rad_s])
    rotating_velocity = relative_velocity-np.cross(frame_omega,delta)
    los_rate = (rotating_velocity-los*np.sum(los*rotating_velocity,axis=1)[:,None])/ranges[:,None]
    angular_rate = np.linalg.norm(los_rate,axis=1)
    phase = np.degrees(np.arccos(np.clip((-los)@sun_direction,-1,1)))
    focal = model.derived(case)[0]
    half_widths = np.array([model.b['W_x'],model.b['W_y']])/(2*focal)
    # Transform to the rotating camera before applying rectangular field limits.
    delta_camera = delta@camera_axes
    velocity_camera = rotating_velocity@camera_axes
    front = delta_camera[:,0]>0
    safe_x = np.where(front,delta_camera[:,0],1.)
    coordinates = delta_camera[:,1:]/safe_x[:,None]
    rates = (velocity_camera[:,1:]*safe_x[:,None]-delta_camera[:,1:]*velocity_camera[:,0,None])/safe_x[:,None]**2
    in_fov = front & np.all(np.abs(coordinates)<=half_widths,axis=1)
    overlap = np.where(front,field_overlap(coordinates,rates,half_widths,model.b['t_int']),0.)
    clear = earth_clear(observer,position)
    illuminated = sunlit_cylindrical(position,sun_direction)
    boresight_sun = float(np.degrees(np.arccos(np.clip(radial@sun_direction,-1,1))))
    sun_safe = boresight_sun >= model.b['sun_exclusion_min']
    visible = in_fov & clear & illuminated & sun_safe
    if geometry_only:
        return {'in_fov':in_fov,'visible':visible}
    optical = model.evaluate(case,ranges*1000,diameter_m=population['diameter_m'],
                             phase_deg=phase,apparent_rate_rad_s=angular_rate,exposure_overlap_s=overlap)
    visible = in_fov & clear & illuminated & sun_safe
    detected = visible & optical['eligible'] & (optical['snr']>=model.b['SNR_min'])
    return {'range_km':ranges,'in_fov':in_fov,'earth_clear':clear,'sunlit':illuminated,
            'sun_safe':np.full(len(ranges),sun_safe),'visible':visible,'detectable':detected,
            'phase_deg':phase,'angular_rate_rad_s':angular_rate,'exposure_overlap_s':overlap,
            'snr':np.where(illuminated,optical['snr'],0.),'unsaturated':optical['unsaturated'],
            'unresolved':optical['unresolved'],'partial_transit':optical['partial_transit'],
            'boresight_sun_deg':boresight_sun,'observer_velocity_km_s':velocity.tolist(),
            'observer_position_km':observer.tolist()}
