"""ESA inclination and optional empirical (e, RAAN, argument of perigee).

An absent catalogue never triggers a fabricated empirical distribution.
"""

import csv
from pathlib import Path
import numpy as np

from .population import EARTH_RADIUS_KM
from .orbits import elements_to_states


def load_empirical_catalogue(path: Path):
    """Read quoted CSV fields correctly and retain donor identity/epoch."""
    dtype = [("catalogue_id", "U20"), ("mean_altitude_km", float), ("perigee_km", float),
             ("apogee_km", float), ("eccentricity", float), ("raan_deg", float),
             ("argument_of_perigee_deg", float), ("epoch_utc", "U40"),
             ("source_epoch_utc", "U40"), ("source_family", "U100"), ("frame", "U10")]
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = [name for name, _ in dtype]
        if reader.fieldnames is None or any(name not in reader.fieldnames for name in required):
            raise ValueError("Faltan columnas en el catálogo")
        rows = [tuple(row[name] for name in required) for row in reader]
    return np.array(rows, dtype=dtype)


def sample_inclinations(reference_dir: Path, perigee_km, rng):
    table = np.genfromtxt(reference_dir / "esa2026_inclination_perigee.csv", delimiter=",", names=True)
    columns = np.unique(table["perigee_min_km"])
    result = np.empty(len(perigee_km))
    borrowed = 0
    # Conditioning in the original 40 km bins, nearest nonempty column if absent.
    requested = np.floor(np.asarray(perigee_km) / 40) * 40
    for h in np.unique(requested):
        indices = np.flatnonzero(requested == h)
        available = columns[np.argmin(np.abs(columns - h))]
        if available != h:
            borrowed += len(indices)
        cell = table[table["perigee_min_km"] == available]
        probability = cell["approximate_count"] / cell["approximate_count"].sum()
        draws = rng.choice(len(cell), size=len(indices), p=probability)
        result[indices] = rng.uniform(cell["inclination_min_deg"][draws], cell["inclination_max_deg"][draws])
    return result, borrowed


def assign_orbital_elements(data, reference_dir: Path, seed=20260202, catalogue=None):
    """Use empirical tuples jointly within altitude neighbourhoods when available.

    Without catalogue, inclination uses circular altitude as perigee proxy;
    e/RAAN/argument of perigee are deliberately absent from the result.
    """
    rng = np.random.default_rng(seed)
    result = {k: np.array(v, copy=True) for k, v in data.items() if k != "eccentricity"}
    h = result["altitude_km"]
    a = EARTH_RADIUS_KM + h
    metadata = {"orbital_seed": seed, "inclination_source": "ESA 2026 Fig. 3.3a",
                "missing_parameters": ["eccentricity", "raan_deg", "argument_of_perigee_deg"],
                "status": "inclination_only; empirical catalogue unavailable",
                "inclination_altitude_condition": "mean altitude as circular perigee proxy",
                "common_epoch_validated": False}
    if catalogue is not None:
        required = ("catalogue_id", "mean_altitude_km", "perigee_km", "apogee_km",
                    "eccentricity", "raan_deg", "argument_of_perigee_deg", "epoch_utc")
        if len(catalogue) == 0 or any(k not in catalogue.dtype.names for k in required):
            raise ValueError("Catálogo empírico vacío o sin columnas requeridas")
        for field in required[1:-1]:
            if not np.isfinite(catalogue[field]).all():
                raise ValueError(f"Campo no finito: {field}")
        if np.any((catalogue["eccentricity"] < 0) | (catalogue["eccentricity"] >= 1)):
            raise ValueError("Excentricidad inválida")
        for field in ("raan_deg", "argument_of_perigee_deg"):
            if np.any((catalogue[field] < 0) | (catalogue[field] >= 360)):
                raise ValueError(f"Ángulo fuera de [0, 360): {field}")
        if np.any(catalogue["perigee_km"] < 200) or np.any(catalogue["apogee_km"] > 2000):
            raise ValueError("El catálogo debe contener órbitas totalmente residentes en 200–2000 km")
        if len(np.unique(catalogue["epoch_utc"])) != 1 or "frame" not in catalogue.dtype.names or not np.all(catalogue["frame"] == "TEME"):
            raise ValueError("Los donantes deben estar sincronizados en una época única y marco TEME")
        selected = np.empty(len(h), dtype=int)
        widened = 0
        maximum_nearest_offset = 0.0
        original_altitude = h.copy()
        boundary_adjusted = 0
        # Joint tuple bootstrap; never draw e, Omega and omega independently.
        for j, altitude in enumerate(h):
            max_e = min(altitude-200, 2000-altitude) / a[j]
            feasible = np.flatnonzero(catalogue["eccentricity"] <= max_e)
            if not len(feasible):
                # No invented/clipped e: shift h minimally inside a feasible
                # interval using the least eccentric empirical donor.
                minimum_e = float(catalogue["eccentricity"].min())
                lower_h = (200+EARTH_RADIUS_KM*minimum_e)/(1-minimum_e)+1e-7
                upper_h = (2000-EARTH_RADIUS_KM*minimum_e)/(1+minimum_e)-1e-7
                if lower_h >= upper_h:
                    raise ValueError("No existe intervalo de altitud compatible con el catálogo")
                altitude = float(np.clip(altitude, lower_h, upper_h))
                h[j], a[j] = altitude, EARTH_RADIUS_KM+altitude
                boundary_adjusted += 1
                max_e = min(altitude-200, 2000-altitude)/a[j]
                feasible = np.flatnonzero(catalogue["eccentricity"] <= max_e)
            distance = np.abs(catalogue["mean_altitude_km"][feasible] - altitude)
            local = feasible[distance <= 100]
            if not len(local):
                widened += 1
                order = np.argsort(distance, kind="stable")[:min(50, len(feasible))]
                local = feasible[order]
                maximum_nearest_offset = max(maximum_nearest_offset, float(distance[order].max()))
            selected[j] = rng.choice(local)
        donors = catalogue[selected]
        result["semi_major_axis_km"] = a
        result["esa_sampled_altitude_km"] = original_altitude
        result["altitude_adjustment_km"] = h-original_altitude
        for field in ("eccentricity", "raan_deg", "argument_of_perigee_deg"):
            result[field] = donors[field].astype(float)
        result["perigee_km"] = a * (1-result["eccentricity"]) - EARTH_RADIUS_KM
        result["apogee_km"] = a * (1+result["eccentricity"]) - EARTH_RADIUS_KM
        result["donor_catalogue_id"] = donors["catalogue_id"]
        result["donor_mean_altitude_km"] = donors["mean_altitude_km"]
        result["donor_altitude_offset_km"] = np.abs(donors["mean_altitude_km"]-h)
        result["donor_local_support"] = result["donor_altitude_offset_km"] <= 100
        result["donor_source_epoch_utc"] = donors["source_epoch_utc"]
        result["donor_family"] = donors["source_family"]
        result["epoch_utc"] = donors["epoch_utc"]
        result["frame"] = donors["frame"]
        families, family_counts = np.unique(donors["source_family"], return_counts=True)
        metadata.update({"missing_parameters": [], "status": "hybrid synthetic population; common-epoch empirical donor elements",
                         "epoch_utc": str(donors["epoch_utc"][0]), "frame": "TEME",
                         "donor_states_synchronized": True, "synthetic_state_epoch_defined": True,
                         "inclination_altitude_condition": "derived perigee",
                         "altitude_neighbourhood_km": 100, "nearest_donor_fallback_objects": widened,
                         "maximum_fallback_altitude_offset_km": maximum_nearest_offset,
                         "maximum_selected_donor_altitude_offset_km": float(result["donor_altitude_offset_km"].max()),
                         "donors_used": int(len(np.unique(selected))),
                         "sampled_family_counts": {str(f): int(n) for f, n in zip(families, family_counts)},
                         "boundary_altitude_adjusted_objects": boundary_adjusted,
                         "maximum_boundary_altitude_adjustment_km": float(np.abs(h-original_altitude).max()),
                         "warning": "Three-family proxy; e/Omega/omega joint only conditional on altitude, inclination independently ESA; no claimed global fidelity"})
    perigee = result.get("perigee_km", h)
    result["inclination_deg"], borrowed = sample_inclinations(reference_dir, perigee, rng)
    metadata["inclination_nearest_column_fallback_objects"] = borrowed
    if catalogue is not None:
        # Uniform mean anomaly, not true anomaly: uniform time along each ellipse.
        phase_rng = np.random.default_rng(seed+1)
        result["mean_anomaly_deg"] = phase_rng.uniform(0, 360, len(h))
        positions, velocities = elements_to_states(a, result["eccentricity"], result["inclination_deg"],
            result["raan_deg"], result["argument_of_perigee_deg"], result["mean_anomaly_deg"])
        for axis, values in zip("xyz", positions.T):
            result[f"{axis}_km"] = values
        for axis, values in zip("xyz", velocities.T):
            result[f"v{axis}_km_s"] = values
        metadata["phase_model"] = "independent uniform mean anomaly [0,360), seed orbital_seed+1"
        metadata["common_epoch_validated"] = True
    return result, metadata
