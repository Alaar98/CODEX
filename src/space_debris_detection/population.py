"""Población aproximada desde curvas ESA; véase Notas del Proyecto.md."""

from pathlib import Path
import numpy as np

EARTH_RADIUS_KM = 6371.0


def load_models(reference_dir: Path):
    density = np.genfromtxt(reference_dir / "esa2026_density_non_manoeuvrable.csv", delimiter=",", names=True)
    sizes = np.genfromtxt(reference_dir / "esa2026_size_cumulative.csv", delimiter=",", names=True)
    # Los segmentos verticales de la curva acumulativa se consolidan tomando
    # el menor N en cada diámetro. Se exige monotonía para invertir la CDF.
    diameter = np.unique(sizes["diameter_m"])
    cumulative = np.array([sizes["cumulative_objects"][sizes["diameter_m"] == d].min() for d in diameter])
    cumulative = np.minimum.accumulate(cumulative)
    grid = np.linspace(200.0, 2000.0, 7201)
    profiles = []
    for field in ("density_gt_1cm_per_km3", "density_gt_10cm_per_km3"):
        profiles.append(10 ** np.interp(grid, density["altitude_km"], np.log10(density[field])))
    small = profiles[0] - profiles[1]
    if np.any(small < 0):
        raise ValueError("La densidad >10 cm supera la densidad >1 cm")
    shell = 4 * np.pi * (EARTH_RADIUS_KM + grid)**2
    return diameter, cumulative, grid, np.array([small, profiles[1]]) * shell


def generate_population(reference_dir: Path, count: int = 50_000, seed: int = 20260201):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("count debe ser un entero positivo")
    diameter, cumulative, altitude, weights = load_models(reference_dir)
    rng = np.random.default_rng(seed)
    # Integral trapezoidal de densidad × volumen diferencial de capa.
    increments = (weights[:, 1:] + weights[:, :-1]) / 2 * np.diff(altitude)
    cdfs = np.column_stack([np.zeros(2), np.cumsum(increments, axis=1)])
    totals = cdfs[:, -1]
    large = rng.random(count) < totals[1] / totals.sum()
    heights = np.empty(count)
    diameters = np.empty(count)
    for group, lower, upper in ((False, 0.01, 0.1), (True, 0.1, float(diameter[-1]))):
        mask = large == group
        n = int(mask.sum())
        cdf = cdfs[int(group)] / totals[int(group)]
        heights[mask] = np.interp(rng.random(n), cdf, altitude)
        knots = np.r_[lower, diameter[(diameter > lower) & (diameter < upper)], upper]
        log_n = np.interp(np.log10(knots), np.log10(diameter), np.log10(cumulative))
        size_cdf = (10**log_n[0] - 10**log_n) / (10**log_n[0] - 10**log_n[-1])
        # Eliminar mesetas para una inversa inequívoca.
        keep = np.r_[True, np.diff(size_cdf) > 0]
        diameters[mask] = 10 ** np.interp(rng.random(n), size_cdf[keep], np.log10(knots[keep]))
    return {"altitude_km": heights, "diameter_m": diameters,
            "semi_major_axis_km": EARTH_RADIUS_KM + heights,
            "eccentricity": np.zeros(count)}, {
        "count": count, "seed": seed, "epoch": "2026-02-01T00:00:00Z",
        "epoch_note": "Hora de referencia convencional; ESA especifica la fecha, no la hora.",
        "counts_by_size": {"1_to_10_cm": int((~large).sum()), "gt_10_cm": int(large.sum())},
        "probability_gt_10_cm": float(totals[1] / totals.sum()),
        "represented_number_from_density_integral": float(totals.sum()),
        "statistical_weight_per_sample": float(totals.sum() / count),
        "max_size_cutoff_m": float(diameter[-1]),
        "orbit_model": "circular; inclination, RAAN, argument of perigee and phase unspecified",
        "warning": "Synthetic approximation, not a MASTER catalogue or a detection prediction",
    }
