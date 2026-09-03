# Deployment

## Local Docker Compose

Run `docker compose build worker` followed by `docker compose up --build -d`. Compose remains the default local path and sets `EXECUTOR_BACKEND=local`; the scheduler launches worker containers through the Docker socket. Prometheus and Grafana are available at `http://localhost:9090` and `http://localhost:3001`.

## Local Kubernetes with kind

Install Docker, kind, kubectl, and GNU Make. Create a cluster and build/load/apply the platform:

```text
kind create cluster --name cloud-ml
make k8s-up
kubectl -n cloud-ml get pods
```

Replace the placeholder values in `infrastructure/kubernetes/configmaps-secrets/platform-secret.yaml` before using a shared cluster. The scheduler runs with `EXECUTOR_BACKEND=kubernetes`, creates indexed Jobs with one Pod per requested worker, and uses Kubernetes DNS such as `backend:8000` and `redis:6379`.

Port-forward the user-facing services:

```text
kubectl -n cloud-ml port-forward svc/frontend 3000:3000
kubectl -n cloud-ml port-forward svc/backend 8000:8000
kubectl -n cloud-ml port-forward svc/grafana 3001:3000
kubectl -n cloud-ml port-forward svc/prometheus 9090:9090
```

Submit an experiment with `resources.workers: 2` through `http://localhost:3000`. Confirm two Pods appear with `kubectl -n cloud-ml get pods -l platform.job`, then inspect the experiment API for per-worker status, heartbeats, failures, and lifecycle history. Kill one Pod with `kubectl -n cloud-ml delete pod <pod>` to exercise the existing retry path. Grafana dashboards should reflect scheduler, worker Pushgateway, and cAdvisor activity.

For minikube, run `minikube start`, replace the `kind load docker-image ...` line in `make k8s-up` with `minikube image load platform/backend:latest ...` (one image per command if required by your minikube version), then run `kubectl apply -k infrastructure/kubernetes`. Use the same port-forward commands.

Tear down with `make k8s-down` and optionally `kind delete cluster --name cloud-ml`.

## Migration path

```text
Local Docker Compose -> Containerized Services -> Kubernetes Deployment -> Distributed Job Execution
```
