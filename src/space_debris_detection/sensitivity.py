"""One-variable-at-a-time alternatives; the nominal population is immutable."""

import csv
import gzip
from pathlib import Path

import numpy as np

from .orbits import elements_to_states, MU_KM3_S2
from .population import EARTH_RADIUS_KM

NUMERIC_FIELDS = {
    "altitude_km", "diameter_m", "semi_major_axis_km", "esa_sampled_altitude_km",
    "altitude_adjustment_km", "eccentricity", "raan_deg", "argument_of_perigee_deg",
    "perigee_km", "apogee_km", "donor_mean_altitude_km", "donor_altitude_offset_km",
    "inclination_deg", "mean_anomaly_deg", "x_km", "y_km", "z_km",
    "vx_km_s", "vy_km_s", "vz_km_s", "statistical_weight", "argument_of_latitude_deg",
}

SCENARIOS = {
    "eccentricity_circular": {"parameter": "eccentricity", "label": "Circular", "model": "e=0; omega retained only as gauge; u=(omega_nominal+M_nominal) mod 360, uniform conditional on omega"},
    "eccentricity_low": {"parameter": "eccentricity", "label": "Lower eccentricity", "model": "e=0.5*e_nominal"},
    "eccentricity_high": {"parameter": "eccentricity", "label": "Higher eccentricity", "model": "q=e_nominal/e_max; e=e_max*2*q/(1+q); smooth bounded transform, no clipping"},
}
for _points in (12, 8, 4):
    for _prefix, _parameter, _word in (("raan", "raan_deg", "planes"),
                                      ("argp", "argument_of_perigee_deg", "positions")):
        SCENARIOS[f"{_prefix}_{_points}_{_word}"] = {
            "parameter": _parameter, "label": f"{_points} equally spaced {_word}",
            "support_points": _points, "spacing_deg": 360/_points,
            "model": f"{_points} exact angles 360*k/{_points}, k=0..{_points-1}; balanced randomized assignment; no angular jitter",
        }

LEGACY_ANGULAR_SCENARIOS = {
    "raan_uniform", "raan_four_planes", "raan_single_plane",
    "argp_uniform", "argp_bimodal", "argp_aligned",
}


def equally_spaced_angles(count, points, seed, stream):
    """Randomize object membership with counts differing by at most one.

    Shared random ranks pair the 12/8/4 cases without correlating assignment
    with the nominal object's size, altitude or inclination.
    """
    if count < points or points <= 0:
        raise ValueError("Need at least one object per angular position")
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    ranks = rng.permutation(count)
    return (ranks*points//count)*(360/points)


def load_population(path: Path):
    """Read a delivered CSV or CSV.gz with numeric columns and circular flag."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, mode="rt", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        columns = reader.fieldnames
    if not rows:
        raise ValueError("Empty nominal population")
    data = {key: np.array([row[key] for row in rows], dtype=float if key in NUMERIC_FIELDS else str)
            for key in columns}
    if "argument_of_perigee_defined" in data:
        flag = data["argument_of_perigee_defined"]
        if not np.isin(flag, ["True", "False"]).all():
            raise ValueError("Invalid circular/perigee flag")
        data["argument_of_perigee_defined"] = flag == "True"
    return data


def load_nominal(path: Path):
    return load_population(path)


def eccentricity_limit(a):
    a = np.asarray(a)
    h = a-EARTH_RADIUS_KM
    limit = np.minimum(h-200, 2000-h)/a
    if np.any(limit <= 0):
        raise ValueError("Nominal semi-major axes must be strictly inside 200–2000 km")
    return limit


def make_scenario(nominal, scenario_id, seed=20261105):
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    data = {key: np.array(values, copy=True) for key, values in nominal.items()}
    n = len(data["eccentricity"])
    if scenario_id.startswith("eccentricity_"):
        e = data["eccentricity"]
        limit = eccentricity_limit(data["semi_major_axis_km"])
        if np.any(e < 0) or np.any(e > limit+1e-12):
            raise ValueError("Nominal eccentricities are incompatible with fixed semi-major axes")
        if scenario_id == "eccentricity_circular":
            data["eccentricity"] = np.zeros(n)
        elif scenario_id == "eccentricity_low":
            data["eccentricity"] = .5*e
        else:
            q = e/limit
            data["eccentricity"] = limit*2*q/(1+q)
    else:
        spec = SCENARIOS[scenario_id]
        stream = 1 if spec["parameter"] == "raan_deg" else 2
        data[spec["parameter"]] = equally_spaced_angles(n, spec["support_points"], seed, stream)
    a, e = data["semi_major_axis_km"], data["eccentricity"]
    data["perigee_km"] = a*(1-e)-EARTH_RADIUS_KM
    data["apogee_km"] = a*(1+e)-EARTH_RADIUS_KM
    # M, a, i and all nonvaried elements stay paired with nominal object IDs.
    r, v = elements_to_states(a, e, data["inclination_deg"], data["raan_deg"],
                              data["argument_of_perigee_deg"], data["mean_anomaly_deg"])
    for axis, values in zip("xyz", r.T):
        data[f"{axis}_km"] = values
    for axis, values in zip("xyz", v.T):
        data[f"v{axis}_km_s"] = values
    node, inc = np.radians(data["raan_deg"]), np.radians(data["inclination_deg"])
    node_axis = np.column_stack((np.cos(node), np.sin(node), np.zeros(n)))
    latitude_axis = np.column_stack((-np.sin(node)*np.cos(inc), np.cos(node)*np.cos(inc), np.sin(inc)))
    latitude = np.degrees(np.arctan2(np.sum(r*latitude_axis, axis=1), np.sum(r*node_axis, axis=1))) % 360
    data["argument_of_latitude_deg"] = latitude
    data["argument_of_perigee_defined"] = e > 1e-10
    data["scenario_id"] = np.full(n, scenario_id)
    data["varied_parameter"] = np.full(n, SCENARIOS[scenario_id]["parameter"])
    data["donor_role"] = np.full(n, "nominal_provenance_only")
    return data


def audit_scenario(nominal, data, scenario_id):
    varied = SCENARIOS[scenario_id]["parameter"]
    n = len(nominal["object_id"])
    for key in ("object_id", "diameter_m", "altitude_km", "semi_major_axis_km", "inclination_deg",
                "epoch_utc", "frame", "mean_anomaly_deg", "statistical_weight"):
        np.testing.assert_array_equal(data[key], nominal[key], err_msg=f"Changed control: {key}")
    for key in ("eccentricity", "raan_deg", "argument_of_perigee_deg"):
        if key != varied:
            np.testing.assert_array_equal(data[key], nominal[key], err_msg=f"Changed second parameter: {key}")
    for key, values in data.items():
        if len(values) != n:
            raise ValueError(f"Wrong population length in {key}")
        if values.dtype.kind in "fc" and not np.isfinite(values).all():
            raise ValueError(f"Nonfinite values in {key}")
    if len(np.unique(data["object_id"])) != n:
        raise ValueError("Duplicate IDs")
    hp, ha = data["perigee_km"], data["apogee_km"]
    if np.any(hp < 200-1e-8) or np.any(ha > 2000+1e-8):
        raise ValueError("Apsides outside requested LEO interval")
    r = np.column_stack([data[f"{k}_km"] for k in "xyz"])
    v = np.column_stack([data[f"v{k}_km_s"] for k in "xyz"])
    radius = np.linalg.norm(r, axis=1)
    energy = np.sum(v*v, axis=1)/2-MU_KM3_S2/radius
    np.testing.assert_allclose(energy, -MU_KM3_S2/(2*data["semi_major_axis_km"]), rtol=1e-12)
    if np.any(radius < hp+EARTH_RADIUS_KM-1e-8) or np.any(radius > ha+EARTH_RADIUS_KM+1e-8):
        raise ValueError("State outside orbital apsides")
    circular_error = None
    if scenario_id == "eccentricity_circular":
        np.testing.assert_array_equal(data["eccentricity"], np.zeros(n))
        expected = (nominal["argument_of_perigee_deg"]+nominal["mean_anomaly_deg"]) % 360
        error = (data["argument_of_latitude_deg"]-expected+180) % 360-180
        circular_error = float(np.max(np.abs(error)))
        if circular_error > 1e-9 or np.any(data["argument_of_perigee_defined"]):
            raise ValueError("Circular latitude/gauge convention failed")
    angular_support = None
    if "support_points" in SCENARIOS[scenario_id]:
        points = SCENARIOS[scenario_id]["support_points"]
        angles, counts = np.unique(data[varied], return_counts=True)
        np.testing.assert_array_equal(angles, np.arange(points)*(360/points))
        if int(counts.max()-counts.min()) > 1:
            raise ValueError("Angular population is not evenly distributed")
        angular_support = {"angles_deg": angles.tolist(), "counts": counts.tolist(),
                           "spacing_deg": 360/points, "no_jitter": True}
    result = {"status": "passed", "objects": n, "varied_parameter": varied,
            "perigee_min_km": float(hp.min()), "apogee_max_km": float(ha.max()),
            "circular_latitude_max_error_deg": circular_error,
            "controls_equal_nominal": True, "other_orbital_elements_equal_nominal": True}
    if angular_support is not None:
        result["angular_support"] = angular_support
    return result
