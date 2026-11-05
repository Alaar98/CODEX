#!/usr/bin/env bash
set -euo pipefail
trace_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$trace_root"
.venv/bin/python scripts/prepare_empirical_catalogue.py \
  --gp 'data/raw/celestrak/Chinese ASAT Test Debris_FENGYUN 1C.csv' \
       'data/raw/celestrak/IRIDIUM 33 Debris.csv' \
       'data/raw/celestrak/COSMOS 2251 Debris.csv' \
  --satcat data/raw/celestrak/satcat.csv \
  --epoch 2026-11-05T00:00:00Z --max-age-days 7
.venv/bin/python scripts/generate_population.py --require-empirical
.venv/bin/python scripts/validate_population.py
