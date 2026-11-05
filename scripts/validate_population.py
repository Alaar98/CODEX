"""Audit the saved full population against geometry, donors and provenance."""

import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from space_debris_detection.orbits import MU_KM3_S2, state_to_elements
from space_debris_detection.orbital_population import load_empirical_catalogue


def main():
    root = Path(__file__).resolve().parents[1]
    generated = root / "data/generated"
    with (generated / "trace_population_50000.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    def numbers(key):
        return np.array([float(r[key]) for r in rows])
    if len(rows) != 50000 or len({r["object_id"] for r in rows}) != 50000:
        raise ValueError("Expected 50,000 unique objects")
    meta = json.loads((generated / "trace_population_metadata.json").read_text())
    donors = load_empirical_catalogue(root / "data/reference/empirical_leo_debris.csv")
    index = {str(row["catalogue_id"]): row for row in donors}
    epoch = meta["orbital_model"]["epoch_utc"]
    for r in rows:
        donor = index[r["donor_catalogue_id"]]
        for key in ("eccentricity", "raan_deg", "argument_of_perigee_deg"):
            if float(r[key]) != float(donor[key]):
                raise ValueError("Donor tuple was modified")
        if r["epoch_utc"] != epoch or r["frame"] != "TEME":
            raise ValueError("Inconsistent epoch or frame")
    a, e, hp, ha = [numbers(k) for k in ("semi_major_axis_km", "eccentricity", "perigee_km", "apogee_km")]
    if not all(np.isfinite(numbers(k)).all() for k in (
            "semi_major_axis_km", "eccentricity", "inclination_deg", "raan_deg", "argument_of_perigee_deg", "mean_anomaly_deg")):
        raise ValueError("Nonfinite orbital elements")
    np.testing.assert_allclose(hp, a*(1-e)-6371, atol=1e-9)
    np.testing.assert_allclose(ha, a*(1+e)-6371, atol=1e-9)
    if hp.min() < 200-1e-8 or ha.max() > 2000+1e-8:
        raise ValueError("Orbit leaves requested region")
    position = np.column_stack([numbers(k+"_km") for k in "xyz"])
    velocity = np.column_stack([numbers("v"+k+"_km_s") for k in "xyz"])
    radius = np.linalg.norm(position, axis=1)
    if not np.isfinite(position).all() or not np.isfinite(velocity).all():
        raise ValueError("Nonfinite Cartesian states")
    if np.any(radius < hp+6371-1e-8) or np.any(radius > ha+6371+1e-8):
        raise ValueError("Position inconsistent with apsides")
    energy = np.sum(velocity**2, axis=1)/2-MU_KM3_S2/radius
    energy_error = float(np.max(np.abs((energy+MU_KM3_S2/(2*a))/energy)))
    if energy_error > 1e-11:
        raise ValueError("Energy invariant failed")
    for j in np.random.default_rng(7).choice(len(rows), 100, replace=False):
        elements = state_to_elements(position[j], velocity[j])
        for key, value in elements.items():
            expected = float(rows[j][key])
            error = abs(value-expected) if key in {"semi_major_axis_km", "eccentricity"} else abs((value-expected+180)%360-180)
            if error > 1e-7:
                raise ValueError(f"Round trip failed for {key}")
    for name, digest in meta["reference_sha256"].items():
        if hashlib.sha256((root/"data/reference"/name).read_bytes()).hexdigest() != digest:
            raise ValueError("Reference hash mismatch")
    provenance = json.loads((root/"data/raw/celestrak/provenance.json").read_text())
    for name, info in provenance["files"].items():
        if hashlib.sha256((root/"data/raw/celestrak"/name).read_bytes()).hexdigest() != info["sha256"]:
            raise ValueError("Original source bytes changed")
    figures = json.loads((generated/"figure_manifest.json").read_text())
    if figures["unavailable"] or any(m["objects_counted"] != len(rows) for m in figures["maps"].values()):
        raise ValueError("Missing parameters or figures discard objects")
    audit = {"status": "passed", "objects": len(rows), "epoch_utc": epoch, "frame": "TEME",
             "checks": ["unique IDs", "finite full elements and Cartesian states", "empirical donor tuples unchanged",
                        "common epoch/frame", "apsides in LEO", "state radius within apsides", "energy invariant",
                        "100 element/state round trips", "source/reference hashes", "all seven maps count 50000"],
             "maximum_relative_energy_error": energy_error,
             "perigee_min_km": float(hp.min()), "apogee_max_km": float(ha.max()),
             "population_sha256": hashlib.sha256((generated/"trace_population_50000.csv").read_bytes()).hexdigest(),
             "limitation": "Computational consistency audit, not validation of global debris representativeness"}
    (generated/"validation.json").write_text(json.dumps(audit, indent=2)+"\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
