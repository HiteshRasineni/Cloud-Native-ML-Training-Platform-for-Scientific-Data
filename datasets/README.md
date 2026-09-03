# Datasets

`sample/` holds the deterministic synthetic HEP-like dataset:
- `generate_sample.py` — generates `cms-run2015_v1.parquet` (~5000 rows: event_id, pt, eta, phi, energy, label; fixed seed).
- `cms-run2015_v1.parquet` — generated artifact (do not commit large data; regenerate via `make sample-dataset`).

Register it in MinIO + the backend with `make register-sample-dataset`.
