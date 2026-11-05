"""Classify debris GP files and propagate donors with SGP4 to one epoch."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

from sgp4.api import Satrec, SGP4_ERRORS, jday
from sgp4 import omm

from space_debris_detection.orbits import MU_KM3_S2, state_to_elements
from space_debris_detection.population import EARTH_RADIUS_KM

DEFAULT_EPOCH = "2026-11-05T00:00:00Z"


def utc_datetime(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)  # CelesTrak GP timestamps are UTC.
    return parsed.astimezone(timezone.utc)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        dialect = csv.Sniffer().sniff(f.read(8192), delimiters=",;")
        f.seek(0)
        return list(csv.DictReader(f, dialect=dialect))


def prepare(gp_path, satcat_path, output, epoch=DEFAULT_EPOCH, max_age_days=7.):
    gp_paths = [gp_path] if isinstance(gp_path, Path) else list(gp_path)
    target = utc_datetime(epoch)
    if max_age_days <= 0 or not math.isfinite(max_age_days):
        raise ValueError("max_age_days must be finite and positive")
    satcat = read_csv(satcat_path)
    classes = {int(r["NORAD_CAT_ID"]): r for r in satcat}
    if len(classes) != len(satcat):
        raise ValueError("SATCAT contains duplicate IDs")
    combined = {}
    duplicate_rows = 0
    for path in gp_paths:
        for r in read_csv(path):
            identity = int(r["NORAD_CAT_ID"])
            if identity in combined:
                duplicate_rows += 1
                old = combined[identity][0]
                if utc_datetime(r["EPOCH"]) < utc_datetime(old["EPOCH"]):
                    continue
                if r["EPOCH"] == old["EPOCH"] and r != old:
                    raise ValueError(f"Conflicting GP rows at same epoch for {identity}")
            combined[identity] = (r, path.stem)
    jd, fraction = jday(target.year, target.month, target.day, target.hour, target.minute,
                        target.second+target.microsecond/1e6)
    rows, rejected = [], {}
    def reject(reason):
        rejected[reason] = rejected.get(reason, 0)+1
    for identity, (r, family) in sorted(combined.items()):
        classification = classes.get(identity)
        if classification is None or classification["OBJECT_TYPE"].strip() not in {"DEB", "R/B"}:
            reject("not_classified_debris_or_rocket_body")
            continue
        if classification.get("OPS_STATUS_CODE", "").strip() in {"+", "P", "B", "S", "X"}:
            reject("operational_object")
            continue
        if classification.get("DECAY_DATE", "").strip():
            reject("decayed")
            continue
        if classification.get("ORBIT_CENTER", "EA").strip() not in {"EA", "EARTH"}:
            reject("not_earth")
            continue
        source_epoch = utc_datetime(r["EPOCH"])
        age_days = abs((target-source_epoch).total_seconds()/86400)
        if age_days > max_age_days:
            reject("epoch_outside_age_window")
            continue
        e, motion, i, raan, argp = (float(r[k]) for k in
            ("ECCENTRICITY", "MEAN_MOTION", "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER"))
        if not all(math.isfinite(v) for v in (e, motion, i, raan, argp)) or not (
                0 <= e < 1 and motion > 0 and 0 <= i <= 180 and 0 <= raan < 360 and 0 <= argp < 360):
            reject("invalid_elements")
            continue
        satellite = Satrec()
        omm_fields = dict(r)
        # sgp4.omm expects fractional seconds and no timezone suffix.
        omm_fields["EPOCH"] = source_epoch.strftime("%Y-%m-%dT%H:%M:%S.%f")
        omm.initialize(satellite, omm_fields)
        error, position, velocity = satellite.sgp4(jd, fraction)
        if error:
            reject("sgp4_"+SGP4_ERRORS.get(error, str(error)))
            continue
        try:
            el = state_to_elements(position, velocity)
        except ValueError:
            reject("nonelliptic_or_invalid_state")
            continue
        a, e = el["semi_major_axis_km"], el["eccentricity"]
        hp, ha = a*(1-e)-EARTH_RADIUS_KM, a*(1+e)-EARTH_RADIUS_KM
        if hp < 200 or ha > 2000:
            reject("outside_resident_200_2000_km")
            continue
        rows.append([identity, r.get("OBJECT_NAME", ""), classification["OBJECT_TYPE"], family,
                     target.isoformat().replace("+00:00", "Z"), r["EPOCH"], age_days, "TEME", a-EARTH_RADIUS_KM,
                     hp, ha, e, el["inclination_deg"], el["raan_deg"], el["argument_of_perigee_deg"]])
    if not rows:
        raise ValueError("No eligible debris donors after classification, age and orbit filters")
    counts_by_family = {}
    for row in rows:
        counts_by_family[row[3]] = counts_by_family.get(row[3], 0)+1
    metadata = {"source": "User-supplied CelesTrak files; raw originals and SHA256 in data/raw/celestrak",
                "source_files_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [*gp_paths, satcat_path]},
                "input_gp_objects": len(combined), "duplicate_rows_removed": duplicate_rows,
                "retained_donors": len(rows), "counts_by_family": counts_by_family, "rejected": rejected,
                "epoch_utc": target.isoformat().replace("+00:00", "Z"), "frame": "TEME",
                "source_epoch_min": min(row[5] for row in rows), "source_epoch_max": max(row[5] for row in rows),
                "max_allowed_epoch_offset_days": max_age_days,
                "earth_radius_km": EARTH_RADIUS_KM, "conversion_mu_km3_s2": MU_KM3_S2,
                "filter": "DEB/RB, nonoperational/nondecayed/geocentric; source epoch within window; osculating hp>=200, ha<=2000 km",
                "propagation": "sgp4 2.27, WGS72 default; two-body instantaneous TEME elements converted with stated mu",
                "warning": "Three breakup families are not representative of all LEO debris; propagated catalogue predictions are not ground truth"}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["catalogue_id", "object_name", "object_type", "source_family", "epoch_utc", "source_epoch_utc",
                         "epoch_offset_days", "frame", "mean_altitude_km", "perigee_km", "apogee_km", "eccentricity",
                         "inclination_deg", "raan_deg", "argument_of_perigee_deg"])
        writer.writerows(rows)
    output.with_suffix(".json").write_text(json.dumps(metadata, indent=2)+"\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gp", required=True, type=Path, nargs="+")
    parser.add_argument("--satcat", required=True, type=Path)
    parser.add_argument("--epoch", default=DEFAULT_EPOCH)
    parser.add_argument("--max-age-days", default=7., type=float)
    parser.add_argument("--output", default=Path("data/reference/empirical_leo_debris.csv"), type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.gp, args.satcat, args.output, args.epoch, args.max_age_days), indent=2))


if __name__ == "__main__":
    main()
