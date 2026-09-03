"""FastAPI application entrypoint."""
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.datasets import router as datasets_router
from app.api.experiments import router as experiments_router
from app.api.jobs import router as jobs_router
from app.api.workers import router as workers_router
from app.core.config import get_settings
from app.core.metrics import http_errors_total

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.3.0")

app.include_router(experiments_router)
app.include_router(datasets_router)
app.include_router(workers_router)
app.include_router(jobs_router)


@app.middleware("http")
async def observe_http_errors(request: Request, call_next):
    response = await call_next(request)
    if response.status_code >= 400 and request.url.path != "/metrics":
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        http_errors_total.labels(path, str(response.status_code)).inc()
    return response


Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
