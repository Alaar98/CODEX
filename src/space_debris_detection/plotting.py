"""Shared scientific publication style; PNG-only output at 300 dpi."""

import os
from pathlib import Path
import tempfile

cache = Path(tempfile.gettempdir()) / "trace-cache"
cache.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(cache / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(cache))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np


def publication_style():
    """Computer Modern math, serif text; no external TeX toolchain required."""
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral"],
        "mathtext.fontset": "cm", "font.size": 11,
        "axes.labelsize": 12, "axes.titlesize": 12, "axes.linewidth": .8,
        "xtick.direction": "in", "ytick.direction": "in",
        "xtick.top": True, "ytick.right": True,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "legend.frameon": False, "savefig.dpi": 300,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "figure.constrained_layout.use": True,
    })


def save_figure(fig, outputs, name):
    outputs.mkdir(parents=True, exist_ok=True)
    fig.savefig(outputs / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def count_map(x, y, xedges, yedges, xlabel, ylabel, title, outputs, name, log_y=False):
    counts, _, _ = np.histogram2d(x, y, bins=(xedges, yedges))
    if int(counts.sum()) != len(x):
        raise ValueError(f"{name}: el histograma pierde objetos")
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    mesh = ax.pcolormesh(xedges, yedges, np.ma.masked_equal(counts.T, 0),
                         cmap="inferno_r", norm=LogNorm(vmin=1, vmax=max(2, counts.max())),
                         shading="flat", rasterized=False)
    if log_y:
        ax.set_yscale("log")
    ax.set(xlabel=xlabel, ylabel=ylabel, title=title,
           xlim=(xedges[0], xedges[-1]), ylim=(yedges[0], yedges[-1]))
    colorbar = fig.colorbar(mesh, ax=ax, pad=.025)
    colorbar.set_label("Number of objects per bin")
    save_figure(fig, outputs, name)
    return {"objects_counted": int(counts.sum()), "altitude_bins": len(xedges)-1,
            "parameter_bins": len(yedges)-1, "maximum_bin_count": int(counts.max())}


def population_figures(data, outputs: Path):
    publication_style()
    h = np.asarray(data["altitude_km"])
    h_edges = np.arange(200, 2001, 40)
    perigee_available = "perigee_km" in data
    coordinate = data.get("perigee_km", h)
    xlabel = (r"Perigee altitude $h_p$ [km] (40 km bins)" if perigee_available
              else r"Mean altitude $a-R_\oplus$ [km] (40 km bins)")
    suffix = "ESA Fig. 3.3a" if perigee_available else "ESA Fig. 3.3a; circular altitude proxy"
    parameters = {
        "inclination_deg": ("inclination", r"Inclination $i$ [deg] (3$^\circ$ bins)", np.arange(0, 181, 3)),
        "raan_deg": ("raan", r"RAAN $\Omega$ [deg] (6$^\circ$ bins)", np.arange(0, 361, 6)),
        "argument_of_perigee_deg": ("argument_of_perigee", r"Argument of perigee $\omega$ [deg] (6$^\circ$ bins)", np.arange(0, 361, 6)),
        "mean_anomaly_deg": ("mean_anomaly", r"Mean anomaly $M$ [deg] (6$^\circ$ bins)", np.arange(0, 361, 6)),
        "eccentricity": ("eccentricity", r"Eccentricity $e$", None),
        "semi_major_axis_km": ("semi_major_axis", r"Semi-major axis $a$ [km]", np.arange(6571, 8372, 40)),
    }
    manifest = {"style": "STIX serif text; Computer Modern mathtext; inferno_r; log count colourbar; 300 dpi PNG",
                "population": "nominal", "format": "PNG", "dpi": 300,
                "population_count": len(h), "maps": {}, "unavailable": []}
    for key, (name, label, edges) in parameters.items():
        if key not in data:
            manifest["unavailable"].append(key)
            # Remove obsolete charts rather than showing a previous, unrelated run.
            for stem in (f"trace_nominal_{name}_vs_altitude", f"trace_nominal_{name}_histogram"):
                for ext in ("pdf", "png"):
                    (outputs / f"{stem}.{ext}").unlink(missing_ok=True)
            continue
        values = np.asarray(data[key], dtype=float)
        if edges is None:
            edges = np.linspace(0, max(float(values.max())*1.001, 1e-4), 61)
        title = "TRACE — synthetic LEO population"
        if key == "inclination_deg":
            title = "TRACE — inclination distribution\n" + suffix
        manifest["maps"][name] = count_map(coordinate, values, h_edges, edges, xlabel, label,
                                                     title, outputs, f"trace_nominal_{name}_vs_altitude")
        counts, _ = np.histogram(values, edges)
        fig, ax = plt.subplots(figsize=(6.6, 4.2))
        ax.stairs(counts, edges, fill=True, color="#007c9e", edgecolor="black", linewidth=.65)
        ax.set(xlabel=label, ylabel="Number of objects", title="TRACE — synthetic LEO population",
               xlim=(edges[0], edges[-1]), ylim=(0, None))
        ax.grid(axis="y", linestyle="--", linewidth=.45, alpha=.45)
        ax.set_axisbelow(True)
        save_figure(fig, outputs, f"trace_nominal_{name}_histogram")
    size_cm = np.asarray(data["diameter_m"])*100
    size_edges = np.geomspace(1, max(float(size_cm.max())*1.001, 10), 61)
    manifest["maps"]["diameter"] = count_map(
        h, size_cm, h_edges, size_edges,
        r"Mean altitude $a-R_\oplus$ [km] (40 km bins)",
        r"Equivalent diameter $d$ [cm] (logarithmic bins)",
        "TRACE — synthetic LEO size distribution", outputs, "trace_nominal_size_vs_altitude", log_y=True)
    small, _ = np.histogram(h[size_cm < 10], h_edges)
    large, _ = np.histogram(h[size_cm >= 10], h_edges)
    if small.sum()+large.sum() != len(h):
        raise ValueError("El histograma de altitud pierde objetos")
    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    ax.bar(h_edges[:-1], small, width=40, align="edge", color="#0099c6", edgecolor="black",
           linewidth=.45, label=r"$1\leq d < 10$ cm")
    ax.bar(h_edges[:-1], large, bottom=small, width=40, align="edge", color="#e69f00",
           edgecolor="black", linewidth=.45, label=r"$d\geq10$ cm")
    ax.set(xlabel=r"Mean altitude $a-R_\oplus$ [km] (40 km bins)", ylabel="Number of objects",
           title="TRACE — synthetic LEO altitude distribution", xlim=(200, 2000), ylim=(0, None))
    ax.grid(axis="both", linestyle="--", linewidth=.45, alpha=.45)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right")
    save_figure(fig, outputs, "trace_nominal_altitude_histogram")
    manifest["altitude_histogram_objects_counted"] = int(small.sum()+large.sum())
    return manifest
