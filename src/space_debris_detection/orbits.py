"""Two-body instantaneous element/state conversions in one inertial frame.

These are conversions at an epoch, not a long-term force/propagation model.
"""

import numpy as np

MU_KM3_S2 = 398600.4418


def state_to_elements(position_km, velocity_km_s):
    r = np.asarray(position_km, dtype=float)
    v = np.asarray(velocity_km_s, dtype=float)
    radius = np.linalg.norm(r)
    angular = np.cross(r, v)
    angular_norm = np.linalg.norm(angular)
    if radius <= 0 or angular_norm <= 0 or not np.isfinite(np.r_[r, v]).all():
        raise ValueError("Invalid Cartesian state")
    node = np.cross([0., 0., 1.], angular)
    node_norm = np.linalg.norm(node)
    eccentricity_vector = np.cross(v, angular)/MU_KM3_S2 - r/radius
    e = np.linalg.norm(eccentricity_vector)
    energy = np.dot(v, v)/2 - MU_KM3_S2/radius
    if energy >= 0 or e >= 1:
        raise ValueError("Only elliptic orbits are supported")
    inclination = np.arccos(np.clip(angular[2]/angular_norm, -1, 1))
    raan = np.arctan2(node[1], node[0]) if node_norm > 1e-10 else 0.
    if e > 1e-10:
        if node_norm > 1e-10:
            omega = np.arctan2(np.dot(np.cross(node, eccentricity_vector), angular)/(node_norm*e*angular_norm),
                               np.dot(node, eccentricity_vector)/(node_norm*e))
        else:
            omega = np.arctan2(eccentricity_vector[1], eccentricity_vector[0]) * np.sign(angular[2])
        true_anomaly = np.arctan2(np.dot(np.cross(eccentricity_vector, r), angular)/(e*radius*angular_norm),
                                  np.dot(eccentricity_vector, r)/(e*radius))
    else:
        omega = 0.
        if node_norm > 1e-10:
            true_anomaly = np.arctan2(np.dot(np.cross(node, r), angular)/(node_norm*radius*angular_norm),
                                      np.dot(node, r)/(node_norm*radius))
        else:
            true_anomaly = np.arctan2(r[1], r[0]) * np.sign(angular[2])
    eccentric_anomaly = np.arctan2(np.sqrt(1-e*e)*np.sin(true_anomaly), e+np.cos(true_anomaly))
    return {"semi_major_axis_km": -MU_KM3_S2/(2*energy), "eccentricity": float(e),
            "inclination_deg": float(np.degrees(inclination)), "raan_deg": float(np.degrees(raan) % 360),
            "argument_of_perigee_deg": float(np.degrees(omega) % 360),
            "mean_anomaly_deg": float(np.degrees(eccentric_anomaly-e*np.sin(eccentric_anomaly)) % 360)}


def elements_to_states(a_km, e, inclination_deg, raan_deg, argument_of_perigee_deg, mean_anomaly_deg):
    a, e, inc, node, omega, mean = np.broadcast_arrays(
        np.asarray(a_km, dtype=float), np.asarray(e, dtype=float),
        *[np.radians(np.asarray(v, dtype=float)) for v in
          (inclination_deg, raan_deg, argument_of_perigee_deg, mean_anomaly_deg)])
    if not all(np.isfinite(v).all() for v in (a, e, inc, node, omega, mean)) or np.any(a <= 0) or np.any((e < 0) | (e >= 1)):
        raise ValueError("Finite elliptic elements required")
    mean = mean % (2*np.pi)
    eccentric_anomaly = np.where(e < .8, mean, np.pi)
    for _ in range(80):
        correction = (eccentric_anomaly-e*np.sin(eccentric_anomaly)-mean)/(1-e*np.cos(eccentric_anomaly))
        eccentric_anomaly = eccentric_anomaly-correction
        if np.max(np.abs(correction)) < 1e-13:
            break
    else:
        raise ValueError("Kepler solver failed to converge")
    x = a*(np.cos(eccentric_anomaly)-e)
    y = a*np.sqrt(1-e*e)*np.sin(eccentric_anomaly)
    factor = np.sqrt(MU_KM3_S2/a)/(1-e*np.cos(eccentric_anomaly))
    vx = -factor*np.sin(eccentric_anomaly)
    vy = factor*np.sqrt(1-e*e)*np.cos(eccentric_anomaly)
    cO, sO, co, so, ci, si = np.cos(node), np.sin(node), np.cos(omega), np.sin(omega), np.cos(inc), np.sin(inc)
    axis_p = np.stack((cO*co-sO*so*ci, sO*co+cO*so*ci, so*si), axis=-1)
    axis_q = np.stack((-cO*so-sO*co*ci, -sO*so+cO*co*ci, co*si), axis=-1)
    return axis_p*x[..., None]+axis_q*y[..., None], axis_p*vx[..., None]+axis_q*vy[..., None]
