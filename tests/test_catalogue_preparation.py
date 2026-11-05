import csv
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_empirical_catalogue import prepare
from space_debris_detection.orbital_population import load_empirical_catalogue


class CataloguePreparationTests(unittest.TestCase):
    def test_classification_filter_and_quoted_names(self):
        # Synthetic fixtures only; not astronomical evidence.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gp, satcat, output = (root / p for p in ("gp.csv", "satcat.csv", "donors.csv"))
            with satcat.open("w", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow(["NORAD_CAT_ID", "OBJECT_TYPE", "DECAY_DATE", "ORBIT_CENTER"])
                writer.writerows([[1, "DEB", "", "EA"], [2, "PAY", "", "EA"],
                                  [3, "R/B", "2020-01-01", "EA"], [4, "DEB", "", "EA"]])
            with gp.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["NORAD_CAT_ID", "OBJECT_NAME", "EPOCH", "ECCENTRICITY", "MEAN_MOTION",
                                 "INCLINATION", "RA_OF_ASC_NODE", "ARG_OF_PERICENTER", "OBJECT_ID",
                                 "MEAN_ANOMALY", "BSTAR", "MEAN_MOTION_DOT", "MEAN_MOTION_DDOT",
                                 "CLASSIFICATION_TYPE", "EPHEMERIS_TYPE", "ELEMENT_SET_NO", "REV_AT_EPOCH"])
                for identity in (1, 2, 3, 4):
                    writer.writerow([identity, "TEST, FIXTURE", "2026-01-01T00:00:00", .001,
                                     14.5 if identity != 4 else 1.0, 98, 359, 90,
                                     "2000-001A", 20, 0, 0, 0, "U", 0, 1, 1])
            meta = prepare(gp, satcat, output, epoch="2026-01-01T00:00:00Z")
            self.assertEqual(meta["retained_donors"], 1)
            self.assertEqual(meta["input_gp_objects"], 4)
            self.assertEqual(sum(meta["rejected"].values()), 3)
            donors = load_empirical_catalogue(output)
            self.assertEqual(len(donors), 1)
            self.assertEqual(donors["catalogue_id"][0], "1")
            self.assertAlmostEqual(donors["raan_deg"][0], 359, delta=.1)
            self.assertEqual(donors["frame"][0], "TEME")
            self.assertTrue(output.with_suffix(".json").exists())
