# Stage documentation index

Each stage writes `reports/stageN_*.json` with validation checks, artifact paths, and pending issues.

The pipeline **stops** if a stage fails validation (`RuntimeError`).

See `README.md` for the stage map and `src/utils/api_contracts.py` for Phase-2 API shapes.
