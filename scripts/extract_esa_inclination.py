"""Extract ESA Fig. 3.3a vector cells; optional dependency: PyMuPDF."""

import csv
import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "trace-cache/matplotlib"))

import fitz
from matplotlib import colormaps
import numpy as np


def main():
    root = Path(__file__).resolve().parents[1]
    ref = root / "data/reference"
    original = json.loads((ref / "extraction.json").read_text())
    pdf = root / "docs/references" / original["source"]
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != original["sha256"]:
        raise ValueError("El PDF difiere del documento calibrado")
    doc = fitz.open(pdf)
    page = doc[67]
    # Plot frame from PDF vectors, tick spacing from log10 count labels.
    left, right = 83.55752563476562, 253.99008178710938
    bottom, top = 352.19842529296875, 181.76585388183594
    log_max = (bottom - top) / 50.97869873046875
    cmap = colormaps["inferno_r"](np.linspace(0, 1, 256))[:, :3]
    rows, residuals = [], []
    for drawing in page.get_drawings():
        r = drawing["rect"]
        if not (drawing["fill"] and len(drawing["items"]) == 4
                and abs(r.width - (right-left)/50) < .001
                and abs(r.height - (bottom-top)/60) < .001
                and r.x0 >= left-.001 and r.x1 <= right+.001
                and r.y0 >= top-.001 and r.y1 <= bottom+.001):
            continue
        distances = np.linalg.norm(cmap - np.array(drawing["fill"]), axis=1)
        index = int(distances.argmin())
        if distances[index] > 1e-5:
            raise ValueError("Color fuera de la paleta calibrada")
        h_bin = round((r.x0-left) / ((right-left)/50))
        i_bin = round((bottom-r.y1) / ((bottom-top)/60))
        rows.append([h_bin*40, (h_bin+1)*40, i_bin*3, (i_bin+1)*3,
                     float(10 ** (index/255*log_max))])
        residuals.append(float(distances[index]))
    if len(rows) != 574 or len({tuple(r[:4]) for r in rows}) != len(rows):
        raise ValueError("Número de celdas inesperado o duplicadas")
    rows.sort()
    with (ref / "esa2026_inclination_perigee.csv").open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["perigee_min_km", "perigee_max_km", "inclination_min_deg",
                         "inclination_max_deg", "approximate_count"])
        writer.writerows(rows)
    metadata = {
        "source": original["source"], "sha256": original["sha256"], "page": 68,
        "figure": "3.3a", "population": "Objects residing in LEO, end of 2025",
        "method": "vector cell bounds; inverse 256-entry inferno_r LUT; log count scale",
        "frame_pdf_points": [left, top, right, bottom],
        "log10_count_max": log_max, "cells_nonempty": len(rows),
        "max_color_residual": max(residuals),
        "count_quantization": "color LUT inversion yields approximate weights, not exact integer counts",
        "zero_cells": "Unpainted cells have zero weight, never one",
    }
    (ref / "esa2026_inclination_extraction.json").write_text(json.dumps(metadata, indent=2)+"\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
