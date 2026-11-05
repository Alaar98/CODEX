"""Ejecutar desde la raíz: .venv/bin/python scripts/generate_population.py."""

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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from space_debris_detection.population import generate_population


def main():
    root = Path(__file__).resolve().parents[1]
    reference = root / "data/reference"
    generated = root / "data/generated"
    outputs = root / "outputs"
    generated.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    data, metadata = generate_population(reference)
    metadata["reference_sha256"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(reference.glob("*.csv"))
    }
    with (generated / "trace_population_50000.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["object_id", *data, "epoch_utc", "statistical_weight"])
        for i in range(metadata["count"]):
            writer.writerow([f"TRACE-{i+1:05d}", *[v[i] for v in data.values()],
                             metadata["epoch"], metadata["statistical_weight_per_sample"]])
    (generated / "trace_population_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    plt.rcParams.update({"font.size": 11})
    fig, ax = plt.subplots(figsize=(12, 7), layout="constrained")
    ax.scatter(data["altitude_km"], data["diameter_m"] * 100, s=3,
               alpha=0.28, color="#176b95", linewidths=0, rasterized=True)
    ax.set(yscale="log", xlim=(200, 2000), ylim=(1, metadata["max_size_cutoff_m"] * 100),
           xlabel="Altitud orbital media [km]", ylabel="Diámetro equivalente [cm]",
           title="TRACE · Población sintética de 50.000 objetos LEO")
    ax.grid(True, which="major", alpha=0.22)
    ax.set_axisbelow(True)
    fig.supxlabel("Aproximación de ESA 2026, figs. 2.8–2.9 · Cada punto representa un objeto\n"
                  "Órbitas circulares · Objetos no maniobrables · No es un catálogo MASTER", fontsize=9)
    fig.savefig(outputs / "trace_size_vs_altitude.png", dpi=200)
    fig.savefig(outputs / "trace_size_vs_altitude.pdf")
    plt.close(fig)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
