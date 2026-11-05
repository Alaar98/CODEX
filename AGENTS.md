# TRACE project guidance

- The mission is TRACE: Tracking and Reacquisition Architecture for Cooperative
  Estimation of Uncorrelated Space Objects. Python, without AI.
- Record modelling assumptions, changes, data provenance and limitations in
  `Notas del Proyecto.md`. Distinguish measured data from synthetic hypotheses.
- All new plots must use the shared scientific publication style in
  `src/space_debris_detection/plotting.py`: serif text, Computer Modern math,
  clean axes, explicit units/bins, vector PDF and 300 dpi PNG. For population
  maps use 2D counts, white empty cells, inferno_r and a logarithmic colourbar.
  Histograms show counts, not density, unless explicitly requested otherwise.
- Never label uniform or assumed orbital distributions as empirical. Preserve
  catalogue origin, selection, dates, frames and limitations. Do not silently
  propagate or relabel GP/TLE mean elements as common-epoch osculating states.
- Use the existing checkout. Do not create a worktree unless explicitly asked.
- Reproduce the full delivered population with `bash scripts/reproduce_population.sh`
  after installing requirements. Its fixed orbital epoch is 2026-11-05T00:00:00Z,
  frame TEME. Do not silently reset it to the earlier inclination-only mode.
- All five original CelesTrak CSV files are archived under data/raw/celestrak.
  Keep their bytes unchanged; provenance.json contains the source hashes.
  The active GP file is not a debris donor. Three-family extrapolation is
  flagged per object and must not be described as globally representative.
