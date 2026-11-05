"""Create nine sensitivity populations, preserving nominal files byte for byte."""

import argparse
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import numpy as np

from space_debris_detection.plotting import publication_style, save_figure, count_map, plt
from space_debris_detection.sensitivity import SCENARIOS, LEGACY_ANGULAR_SCENARIOS, load_nominal, make_scenario, audit_scenario


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    generated = root/"data/generated"
    nominal_path = generated/"trace_population_50000.csv"
    protected = [nominal_path, generated/"trace_population_metadata.json", generated/"validation.json"]
    original_hashes = {p.name: digest(p) for p in protected}
    nominal = load_nominal(nominal_path)
    if len(nominal["object_id"]) != 50000:
        raise ValueError("Expected the existing 50,000-object nominal population")
    destination, figures = generated/"sensitivity", root/"outputs/sensitivity"
    destination.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    retired_paths = []
    old_manifest = destination/"manifest.json"
    if old_manifest.exists():
        previous = json.loads(old_manifest.read_text())
        for name, record in previous["scenarios"].items():
            if name in SCENARIOS:
                continue
            if name not in LEGACY_ANGULAR_SCENARIOS:
                raise ValueError(f"Unknown old scenario; preserve it for review: {name}")
            population_path, metadata_path = destination/f"{name}.csv.gz", destination/f"{name}.json"
            if population_path.exists() and digest(population_path) != record["sha256"]:
                raise ValueError(f"Old population was edited; refusing to remove {name}")
            if metadata_path.exists() and json.loads(metadata_path.read_text()) != record:
                raise ValueError(f"Old metadata was edited; refusing to remove {name}")
            retired_paths.extend([population_path, metadata_path])
            retired_paths.extend(figures/f"{name}_vs_altitude.{ext}" for ext in ("png", "pdf"))
    manifest = {"seed": args.seed, "nominal": {"file": "../trace_population_50000.csv",
        "sha256": original_hashes[nominal_path.name], "role": "unchanged nominal"},
        "population_count": 10, "alternative_populations": 9, "objects_per_population": 50000,
        "epoch_utc": str(nominal["epoch_utc"][0]), "frame": "TEME",
        "sampling": "one variable at a time; fixed object IDs, sizes, a, i, M, epoch and frame",
        "origin": "sensitivity hypotheses; alternatives are not claimed empirical distributions",
        "scenarios": {}}
    publication_style()
    groups = {
        "eccentricity": ("eccentricity", r"Eccentricity $e$", np.linspace(0, max(float(nominal["eccentricity"].max())*2, .01), 81)),
        "raan_deg": ("raan", r"RAAN $\Omega$ [deg]", np.arange(0, 361, 6)),
        "argument_of_perigee_deg": ("argument_of_perigee", r"Argument of perigee $\omega$ [deg]", np.arange(0, 361, 6)),
    }
    for parameter, (stem, label, edges) in groups.items():
        fig, ax = plt.subplots(figsize=(7.2, 4.5))
        counts, _ = np.histogram(nominal[parameter], edges)
        ax.stairs(counts, edges, color="black", linewidth=1.6, label="Nominal", zorder=5)
        for color, (name, spec) in zip(("#0072b2", "#d55e00", "#009e73"),
                ((name, spec) for name, spec in SCENARIOS.items() if spec["parameter"] == parameter)):
            data = make_scenario(nominal, name, args.seed)
            audit = audit_scenario(nominal, data, name)
            path = destination/f"{name}.csv.gz"
            # Fixed gzip header gives reproducible bytes on repeated runs.
            with path.open("wb") as raw:
                with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
                    with io.TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                        writer = csv.writer(text, lineterminator="\n")
                        writer.writerow(data)
                        writer.writerows(zip(*data.values()))
            metadata = {**spec, "scenario_id": name, "seed": args.seed, "file": path.name,
                        "sha256": digest(path), "nominal_sha256": original_hashes[nominal_path.name],
                        "donor_fields": "inherited nominal lineage, not empirical donors for changed elements",
                        "audit": audit}
            (destination/f"{name}.json").write_text(json.dumps(metadata, indent=2)+"\n")
            manifest["scenarios"][name] = metadata
            counts, _ = np.histogram(data[parameter], edges)
            if int(counts.sum()) != 50000:
                raise ValueError("Comparison histogram loses objects")
            ax.stairs(counts, edges, color=color, linewidth=1.1, label=spec["label"])
            count_map(data["altitude_km"], data[parameter], np.arange(200, 2001, 40), edges,
                      r"Mean altitude $a-R_\oplus$ [km] (40 km bins)", label,
                      f"TRACE — {spec['label']}", figures, "trace_"+name+"_vs_altitude")
        ax.set(xlabel=label, ylabel="Number of objects", xlim=(edges[0], edges[-1]),
               title="TRACE — one-variable sensitivity populations", ylim=(0, None))
        ax.grid(axis="y", linestyle="--", linewidth=.45, alpha=.4)
        if parameter == "eccentricity":
            ax.set_yscale("log")
            ax.set_ylim(.8, None)
        ax.set_axisbelow(True)
        ax.legend(fontsize=9)
        comparison_names = {
            "eccentricity": "trace_comparison_nominal_eccentricity_circular_low_high",
            "raan": "trace_comparison_nominal_raan_12_8_4_planes",
            "argument_of_perigee": "trace_comparison_nominal_argp_12_8_4_positions",
        }
        save_figure(fig, figures, comparison_names[stem])
    for p in protected:
        if digest(p) != original_hashes[p.name]:
            raise ValueError("Nominal file was modified")
    manifest["nominal_files_unchanged"] = original_hashes
    for p in retired_paths:
        p.unlink(missing_ok=True)
    (destination/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"alternatives": 9, "objects_each": 50000, "nominal_unchanged": True,
                      "destination": str(destination)}, indent=2))


if __name__ == "__main__":
    main()
