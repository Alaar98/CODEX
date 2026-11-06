"""Generate conditional instrument curves, without modifying populations."""

import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import numpy as np

from space_debris_detection.optical_validation import load_baseline, OpticalModel, StudyCase, paper_reference
from space_debris_detection.plotting import publication_style, save_figure, plt


def main():
    root = Path(__file__).resolve().parents[1]
    workbook = next((root/"docs/references").glob("*.xlsx"))
    b = load_baseline(workbook)
    model = OpticalModel(b)
    nominal = StudyCase((b["D_ap_min"]+b["D_ap_max"])/2,
                        (b["FOV_min"]+b["FOV_max"])/2, 60., b["albedo_nom"], 5000.)
    data_dir, outputs = root/"data/generated/optical", root/"outputs/optical"
    data_dir.mkdir(parents=True, exist_ok=True)
    protected = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (root/"data/generated").rglob("*.csv*") if "optical" not in p.parts}
    publication_style()
    sizes = np.geomspace(.01, 10, 61)
    ranges = np.geomspace(1, 2e7, 2049)
    groups = {
        "phase": [(replace(nominal, phase_deg=v), rf"$\alpha={v:g}^\circ$") for v in (0, 30, 60, 85)],
        "albedo": [(replace(nominal, albedo=b[k]), rf"$p={b[k]:g}$") for k in ("albedo_pess", "albedo_nom", "albedo_opt")],
        "fov": [(replace(nominal, fov_deg=v), rf"FOV $={v:g}^\circ$") for v in (b["FOV_min"], nominal.fov_deg, b["FOV_max"])],
        "aperture": [(replace(nominal, aperture_m=v), rf"$D={v*1000:g}$ mm") for v in (b["D_ap_min"], nominal.aperture_m, b["D_ap_max"])],
        "velocity": [(replace(nominal, transverse_speed_m_s=v), rf"$v_\perp={v/1000:g}$ km/s") for v in (100, 1000, 5000, 10000, 15000)],
    }
    focal, plate_scale, area_eff = model.derived(nominal)
    manifest = {"workbook": workbook.name, "workbook_sha256": b.source_sha256,
                "baseline_si": b.values, "nominal_instrument_case": asdict(nominal),
                "size_grid_m": sizes.tolist(), "range_grid_m": ranges.tolist(),
                "range_scan": "all sampled eligible intervals refined by 32 bisections; finite-grid narrow windows may be missed",
                "magnitude_range_reference_m": 100000., "figures": [],
                "populations_used": "none; standalone conditional instrument study",
                "saturation_assessed": True, "full_well_gain": "highest_pixel_gain",
                "full_well_e_per_pixel": b["FWC_high_gain"],
                "low_gain_full_well": {"relation": ">", "value_e_per_pixel": b["FWC_low_gain_lower_bound"]},
                "adc_saturation_assessed": False, "mission_detection_counts_computed": False}
    manifest["groups"] = {key: [{"label": label, **asdict(case)} for case, label in cases]
                          for key, cases in groups.items()}
    manifest["nominal_derived"] = {"focal_m": focal, "f_number": focal/nominal.aperture_m,
        "plate_scale_rad_pixel": plate_scale, "effective_area_m2": area_eff,
        "full_transit_lower_range_m": model.transit_lower_range(nominal)}
    manifest["radiometric_assumptions"] = {
        "albedo": "geometric", "background_system": "AB; flat Fnu per arcsec2 over band",
        "solar_model": "5772 K blackbody, bolometric normalization 1361 W/m2 at 1 AU",
        "solar_photons_in_band_m2_s": model.solar_photons_m2_s,
        "psf_extraction": "horizontal uniform streak convolved with Gaussian; 3-sigma padding capped at short-axis field width; conservative fixed enclosed fraction",
        "partial_transits": "accepted at SNR >= 5 with all other eligibility criteria; object time=min(77 ms, central crossing time); maximum temporal overlap; background/dark integrate full exposure",
        "full_transit_boundary": "diagnostic only, never rejects a partial transit",
        "saturation": "expected charge in worst-aligned central pixel incl. sky and dark; reject >= high-gain full well",
        "attitude": "circular LVLH at 450 km; zenith LOS; positive along-track transverse relative motion",
        "not_modelled": ["ADC clipping", "full-well uncertainty", "platform shadow", "Earth eclipse",
                         "mission encounter geometry", "resolved-target photometry", "off-axis response"]}

    def finish(fig, name, caption):
        fig.supxlabel(caption, fontsize=8)
        save_figure(fig, outputs, name)
        manifest["figures"].append(name+".png")

    caption = (rf"Reference: $D={nominal.aperture_m*1000:g}$ mm, FOV $={nominal.fov_deg:g}^\circ$, "
               rf"$p={nominal.albedo:g}$, $\alpha={nominal.phase_deg:g}^\circ$, $v_\perp={nominal.transverse_speed_m_s/1000:g}$ km/s"
               f"\nCircular observer at 450 km; high-gain full well = {b['FWC_high_gain']/1000:g} ke"+r"$^-$ per pixel")
    for group, cases in {"nominal": [(nominal, "Reference")], **groups}.items():
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        records = []
        for case_index, (case, label) in enumerate(cases):
            intervals = [model.range_intervals(case, float(d), ranges) for d in sizes]
            upper = np.array([max((iv["upper_m"] for iv in ivs), default=np.nan) for ivs in intervals])
            censored = np.array([bool(ivs and ivs[-1]["upper_censored"]) for ivs in intervals])
            line, = ax.loglog(sizes*1000, np.where(censored, np.nan, upper)/1000, label=label)
            if censored.any():
                ax.scatter(sizes[censored]*1000, upper[censored]/1000, marker="^", s=16,
                           color=line.get_color(), label="Exceeds distance scan" if group=="nominal" else None)
            ax.axhline(model.transit_lower_range(case)/1000, color=line.get_color(), linestyle="--", linewidth=.8)
            lower = np.array([ivs[0]["lower_m"] if ivs else np.nan for ivs in intervals])/1000
            ax.loglog(sizes*1000, lower, color="crimson" if group=="nominal" else line.get_color(),
                      linewidth=1., linestyle="-.", label="Lower eligible boundary" if group=="nominal" else None)
            for d, ivs in zip(sizes, intervals):
                records.append({"case": asdict(case), "diameter_m": float(d), "intervals": ivs})
            if group == "nominal":
                for interval_index in range(max(map(len, intervals), default=0)):
                    lo = np.array([ivs[interval_index]["lower_m"] if len(ivs)>interval_index else np.nan for ivs in intervals])/1000
                    hi = np.array([ivs[interval_index]["upper_m"] if len(ivs)>interval_index else np.nan for ivs in intervals])/1000
                    ax.fill_between(sizes*1000, lo, hi, color="#e6c84b", alpha=.5,
                                    label="Eligible model interval" if interval_index==0 else None)
        ax.set(xlabel="Equivalent diameter [mm]", ylabel="Instrument–object distance [km]",
               title="TRACE — conditional optical range", xlim=(10, 10000))
        ax.grid(which="major", alpha=.3, linestyle="--")
        ax.legend(fontsize=9)
        finish(fig, f"trace_instrument_reference_range_vs_size_{group}",
               caption+"\nSolid: upper; dash-dot: lower eligible boundary; dashed: full-exposure boundary (not a rejection); triangles: distance-scan limit")
        (data_dir/f"range_vs_size_{group}.json").write_text(json.dumps(records, indent=2)+"\n")
        with (data_dir/f"range_vs_size_{group}.csv").open("w", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["case_index", "diameter_m", "interval_index", "lower_m", "upper_m", "lower_censored", "upper_censored", "lower_constraints"])
            for j, record in enumerate(records):
                for k, interval in enumerate(record["intervals"]):
                    writer.writerow([j//len(sizes), record["diameter_m"], k, interval["lower_m"], interval["upper_m"],
                                     interval["lower_censored"], interval["upper_censored"], ";".join(interval["lower_constraints"])])
        if group == "nominal":
            continue
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        rows = []
        for j, (case, label) in enumerate(cases):
            result = model.evaluate(case, ranges, diameter_m=.1)
            db = 10*np.log10(result["snr"])
            line, = ax.semilogx(ranges/1000, np.where(result["eligible"],db,np.nan), label=label)
            ax.semilogx(ranges/1000,np.where(~result["eligible"],db,np.nan),
                        color=line.get_color(),linestyle=":",alpha=.5)
            rows.extend(zip(np.full(len(ranges), j), ranges, result["snr"], result["eligible"],
                            result["peak_pixel_e"], result["unsaturated"], result["full_transit"], result["unresolved"], result["partial_transit"], result["visible_time_s"]))
        ax.axhline(10*np.log10(b["SNR_min"]), color="crimson", linestyle="--", label=f"SNR = {b['SNR_min']:g}")
        ax.set(xlabel="Instrument–object distance [km]", ylabel=r"$10\log_{10}(\mathrm{SNR})$ [dB]",
               title="TRACE — 10 cm target; conditional point-source model")
        ax.legend(fontsize=9)
        ax.grid(alpha=.3, linestyle="--")
        finish(fig, f"trace_instrument_reference_snr_vs_range_{group}", caption+"\nDotted: saturated or outside point-source/solar domain; flags provided in CSV")
        with (data_dir/f"snr_vs_range_{group}.csv").open("w", newline="") as f:
            w = csv.writer(f, lineterminator="\n"); w.writerow(["case_index", "range_m", "snr_linear", "eligible",
                "peak_pixel_e", "unsaturated", "full_transit", "unresolved", "partial_transit", "visible_time_s"]); w.writerows(rows)
        if group not in {"fov", "aperture", "velocity"}:
            continue
        fig, ax = plt.subplots(figsize=(7.2, 4.8))
        magnitude = np.linspace(0, 23, 300)
        rows = []
        for j, (case, label) in enumerate(cases):
            result = model.evaluate(case, 100000., magnitude_ab=magnitude)
            db = 10*np.log10(result["snr"])
            line, = ax.plot(magnitude,np.where(result["unsaturated"],db,np.nan),label=label)
            ax.plot(magnitude,np.where(~result["unsaturated"],db,np.nan),
                    color=line.get_color(),linestyle=":",alpha=.5)
            rows.extend(zip(np.full(len(magnitude), j), magnitude, result["snr"], result["peak_pixel_e"],result["unsaturated"]))
        ax.axhline(10*np.log10(b["SNR_min"]), color="crimson", linestyle="--", label=f"SNR = {b['SNR_min']:g}")
        ax.set(xlabel="Equivalent band AB magnitude", ylabel=r"$10\log_{10}(\mathrm{SNR})$ [dB]",
               title="TRACE — SNR versus apparent magnitude")
        ax.legend(fontsize=9); ax.grid(alpha=.3, linestyle="--")
        finish(fig, f"trace_instrument_reference_snr_vs_magnitude_{group}", caption+"\nMotion at 100 km; flat-AB equivalent magnitude; dotted curves exceed full well")
        with (data_dir/f"snr_vs_magnitude_{group}.csv").open("w", newline="") as f:
            w=csv.writer(f, lineterminator="\n"); w.writerow(["case_index", "magnitude_ab", "snr_linear", "peak_pixel_e", "unsaturated"]); w.writerows(rows)
    manifest["paper_reference"] = paper_reference()
    for name, sha in protected.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=sha:
            raise ValueError("Population was changed")
    manifest["population_hashes_unchanged"] = protected
    (data_dir/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    print(json.dumps({"figures": len(manifest["figures"]), "reference": asdict(nominal),
                      "paper_reference": manifest["paper_reference"]}, indent=2))


if __name__ == "__main__":
    main()
