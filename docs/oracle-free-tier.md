# Oracle Cloud Free Tier + k3s (Option B)

## Why this target
Oracle Free Tier is TWO things: (a) $300 trial credits for 30 days (expire, paid resources reclaimed), (b) Always Free: 2 Ampere OCPUs + 12GB RAM total + 2x AMD micro VMs + 200GB storage + 10TB egress, never expires, stays running after trial. Signup usually requires mobile + credit card (not charged unless you upgrade). Catches: home-region locked, Out of host capacity retries, idle (<20% cpu/net/mem for 7d) reclaim. So: control plane + CPU workers on 2 OCPU/12GB ARM, optional GPU later via RunPod.

## What changed in code
- `backend/app/schemas/experiment.py`: `resources` now has `gpu`, `node_selector`, `tolerations_json` is supported via executor.
- `scheduler/executors/kubernetes/executor.py`: `_build_resources()` maps `cpu/memory/gpu` to `V1ResourceRequirements` (requests==limits, `nvidia.com/gpu` when >0); `node_selector` + tolerations passed to PodSpec.
- `worker/Dockerfile.gpu`: CUDA 12.1 runtime image for GPU workers. Build with `make k8s-build-gpu`.
- `scheduler/tests/test_kubernetes_executor.py`: asserts resources/GPU/nodeSelector.

## Signup steps (you do this)
1. signup at cloud.oracle.com (email + phone + credit card verify, not charged unless you upgrade). Choose home region carefully (Always Free only there). Create compartment `cloud-ml`.
2. Launch Ampere VM: Shape `VM.Standard.A1.Flex`, 2 OCPU, 12GB (Always Free limit — do NOT exceed or instances disabled+deleted after 30d), Ubuntu 22.04, open ports 22,3000,8000,3001,6443.
3. SSH in, install k3s: `make oracle-k3s-install` or `curl -sfL https://get.k3s.io | sh -`.
4. `pip install oci-cli` optional; install `kubectl`, `kustomize`.
5. Create GHCR PAT (github.com/settings/tokens, `write:packages`), `docker login ghcr.io`.
6. Edit `platform-secret.yaml` placeholders, `kubectl apply -k infrastructure/kubernetes`.
7. Build+push: `docker build -t ghcr.io/YOU/cloud-ml-worker:latest ./worker && docker push ...` (repeat backend/scheduler/frontend), update `WORKER_IMAGE` in `platform-config.yaml`.
8. Submit: `resources: {workers: 1, cpu: 500m, memory: 2Gi, gpu: 0}` for ARM CPU. For GPU: rent RunPod, install nvidia device plugin, set `gpu: 1` + nodeSelector.
