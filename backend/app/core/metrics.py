"""Prometheus metrics for the backend API."""
from prometheus_client import Counter

http_errors_total = Counter(
    "http_errors_total",
    "HTTP responses with status code 400 or higher",
    ("path", "status_code"),
)
experiments_submitted_total = Counter(
    "experiments_submitted_total", "Experiments accepted by the API"
)