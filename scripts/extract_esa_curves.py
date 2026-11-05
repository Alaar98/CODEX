"""Reextraer curvas del PDF adjunto; requiere PyMuPDF (solo extracción).

Ejecutar desde la raíz con un Python que tenga PyMuPDF instalado.
Los índices y calibraciones están ligados al SHA-256 registrado.
"""

import csv
import hashlib
import json
from pathlib import Path

import fitz


def main():
    root = Path(__file__).resolve().parents[1]
    reference = root / "data/reference"
    meta = json.loads((reference / "extraction.json").read_text())
    source = root / "docs/references" / meta["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("El PDF no coincide con el documento calibrado")
    doc = fitz.open(source)
    paths = doc[meta["page"] - 1].get_drawings()
    cal = meta["calibration_pdf_points"]

    def points(index):
        result = []
        for item in paths[index]["items"]:
            if item[0] != "l":
                raise ValueError("Se esperaba una polilínea")
            result.extend((v.x, v.y) for v in item[1:])
        return sorted(set(result))

    with (reference / "esa2026_size_cumulative.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["diameter_m", "cumulative_objects"])
        for x, y in points(meta["vector_paths"]["size"]):
            diameter = 10 ** (-6 + (x-cal["size_x_at_1e_minus_6_m"]) /
                             (cal["size_x_at_1e_minus_5_m"]-cal["size_x_at_1e_minus_6_m"]))
            number = 10 ** (2 + (cal["size_y_at_1e2"]-y)*3 /
                           (cal["size_y_at_1e2"]-cal["size_y_at_1e5"]))
            writer.writerow([diameter, number])
    with (reference / "esa2026_density_non_manoeuvrable.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["altitude_km", "density_gt_1cm_per_km3", "density_gt_10cm_per_km3"])
        small = points(meta["vector_paths"]["non_manoeuvrable_gt_1cm"])
        large = points(meta["vector_paths"]["non_manoeuvrable_gt_10cm"])
        for (x, y), (xx, yy) in zip(small, large, strict=True):
            if abs(x-xx) > 1e-4:
                raise ValueError("Mallas de altitud diferentes")
            altitude = 250 + (x-cal["altitude_x_at_250_km"])*250 / (cal["altitude_x_at_500_km"]-cal["altitude_x_at_250_km"])
            def density(py):
                return 10 ** (-8 + (cal["density_y_at_1e_minus_8"]-py) /
                              (cal["density_y_at_1e_minus_8"]-cal["density_y_at_1e_minus_7"]))
            writer.writerow([altitude, density(y), density(yy)])


if __name__ == "__main__":
    main()
