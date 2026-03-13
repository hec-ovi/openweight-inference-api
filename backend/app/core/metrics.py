"""Prometheus metrics definitions."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "openweight_http_requests_total",
    "Total HTTP requests handled by the gateway.",
    ["method", "path", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "openweight_http_request_duration_seconds",
    "Gateway request latency in seconds.",
    ["method", "path"],
)

STREAM_DURATION = Histogram(
    "openweight_stream_duration_seconds",
    "Time spent proxying upstream SSE streams.",
    ["endpoint", "model_profile"],
)

UPSTREAM_FAILURES = Counter(
    "openweight_upstream_failures_total",
    "Upstream failures while calling vLLM.",
    ["endpoint", "reason"],
)

READINESS_STATUS = Gauge(
    "openweight_readiness_status",
    "Readiness state of the gateway.",
)

