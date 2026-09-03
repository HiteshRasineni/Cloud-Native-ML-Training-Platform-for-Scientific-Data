.PHONY: up down build test logs migrate sample-dataset register-sample-dataset k8s-up k8s-down k8s-logs

up: ## Start the full stack (builds worker image first)
	docker compose build worker
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

test:
	cd backend && python -m pytest
	cd worker && python -m pytest

migrate:
	docker compose exec backend alembic upgrade head

logs:
	docker compose logs -f backend scheduler

sample-dataset: ## Generate the deterministic sample parquet (via a pinned container)
	docker run --rm -v "$(CURDIR)/datasets/sample":/data python:3.12-slim \
		sh -c "pip install -q numpy pandas pyarrow && python /data/generate_sample.py --out /data/cms-run2015_v1.parquet"

register-sample-dataset: sample-dataset ## Upload sample to MinIO + register as cms-run2015:v1
	docker compose exec backend python scripts/register_sample_dataset.py

k8s-up: ## Build images, load them into kind, and apply the Kubernetes overlay
	docker build -t platform/backend:latest ./backend
	docker build -t platform/scheduler:latest ./scheduler
	docker build -t platform/training-worker:latest ./worker
	docker build -t platform/frontend:latest ./frontend
	kind load docker-image platform/backend:latest platform/scheduler:latest platform/training-worker:latest platform/frontend:latest
	kubectl apply -k infrastructure/kubernetes

k8s-down: ## Remove the Phase 5 namespace and all namespaced resources
	kubectl delete namespace cloud-ml --ignore-not-found

k8s-logs: ## Tail scheduler logs and the most recent training worker logs
	kubectl logs -n cloud-ml deploy/scheduler --tail=100
	kubectl logs -n cloud-ml -l platform.job --all-containers=true --tail=100
