"""Ejecutar desde la raíz: .venv/bin/python scripts/generate_population.py."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

# La máquina cloud puede tener HOME de solo lectura.
cache = Path(tempfile.gettempdir()) / "trace-cache"
cache.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache))

from space_debris_detection.population import generate_population
from space_debris_detection.orbital_population import assign_orbital_elements, load_empirical_catalogue
from space_debris_detection.plotting import population_figures


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, help="CSV de donantes clasificados, preparado con prepare_empirical_catalogue.py")
    parser.add_argument("--inclination-only", action="store_true", help="Generar explícitamente una salida parcial sin donantes")
    parser.add_argument("--require-empirical", action="store_true", help="No generar salida parcial si falta el catálogo")
    args = parser.parse_args()
    if args.inclination_only and (args.catalogue is not None or args.require_empirical):
        parser.error("--inclination-only no es compatible con opciones de catálogo")
    catalogue_path = args.catalogue
    if catalogue_path is None and not args.inclination_only:
        bundled = root / "data/reference/empirical_leo_debris.csv"
        if bundled.exists():
            catalogue_path = bundled
    if args.require_empirical and catalogue_path is None:
        parser.error("Se requiere --catalogue; no hay sustitución uniforme o circular empírica")
    catalogue = None
    if catalogue_path is not None:
        catalogue = load_empirical_catalogue(catalogue_path)
    reference = root / "data/reference"
    generated = root / "data/generated"
    outputs = root / "outputs"
    generated.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    data, metadata = generate_population(reference)
    data, orbital_metadata = assign_orbital_elements(data, reference, catalogue=catalogue)
    metadata.pop("epoch")
    metadata.pop("epoch_note")
    metadata.pop("orbit_model")
    metadata["esa_population_reference_date"] = "2026-02-01"
    metadata["orbital_model"] = orbital_metadata
    if catalogue_path is not None:
        metadata["empirical_catalogue"] = {
            "file": catalogue_path.name,
            "sha256": hashlib.sha256(catalogue_path.read_bytes()).hexdigest(),
        }
        source_metadata = catalogue_path.with_suffix(".json")
        if source_metadata.exists():
            metadata["empirical_catalogue"]["preparation"] = json.loads(source_metadata.read_text())
    metadata["reference_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(reference.glob("*.csv"))
    }
    with (generated / "trace_population_50000.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["object_id", *data, "esa_population_reference_date", "statistical_weight"])
        for i in range(metadata["count"]):
            writer.writerow([f"TRACE-{i+1:05d}", *[v[i] for v in data.values()],
                             metadata["esa_population_reference_date"], metadata["statistical_weight_per_sample"]])
    (generated / "trace_population_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    manifest = population_figures(data, outputs)
    (outputs / "figure_manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
