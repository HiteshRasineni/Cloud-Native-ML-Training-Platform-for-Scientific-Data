# GitHub Codespaces (Option B, no card)

Fastest no-card path to run `EXECUTOR_BACKEND=kubernetes` for real.

## 1. Launch (you do this, 2 min)

1. Push this repo to GitHub (already at `HiteshRasineni/Cloud-Native-ML-Training-Platform-for-Scientific-Data`).
2. On GitHub: `Code -> Codespaces -> Create codespace on main` (machine: 4-core if available).
3. Wait for `postCreateCommand` (installs `kind`). Free quota: 120 core-hrs/mo + 15GB, sleeps after 30min idle.

I don't have access to create Codespaces for you — it's tied to your GitHub login/session. You click Create.

## 2. Inside Codespace terminal

```bash
# Compose path (simplest, validates full stack):
docker compose build worker
docker compose up -d --build
docker compose exec backend python scripts/register_sample_dataset.py
# UI: PORTS tab -> 3000 (frontend), 8000 (backend), 3001 (grafana), 5000 (mlflow)

# Kubernetes path (validates new executor resources):
kind create cluster --name cloud-ml
make k8s-up
kubectl -n cloud-ml get pods
kubectl -n cloud-ml port-forward svc/frontend 3000:3000 &
kubectl -n cloud-ml port-forward svc/grafana 3001:3000 &
```

Submit via forwarded frontend URL:
```json
{"experiment": {"name": "codespaces-smoke"}, "dataset": {"name": "cms-run2015", "version": "v1"},
 "model": {"type": "dummy"}, "resources": {"workers": 1, "cpu": "500m", "memory": "1Gi", "gpu": 0},
 "training": {"epochs": 2}}
```
Confirm `kubectl -n cloud-ml get jobs`, container `resources.limits.cpu==500m`, worker `COMPLETED`.

## 3. Limits

No GPU in free Codespaces (CPU-only). Quota burns fast — `gh codespace stop` when done. For GPU training later: RunPod + `worker/Dockerfile.gpu` + `gpu: 1`.
