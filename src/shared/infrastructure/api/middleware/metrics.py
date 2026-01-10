"""
Prometheus metrics middleware.
Collects application metrics for monitoring and alerting.
"""

# Standard library
from time import time

# Third-party
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Metrics definitions
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
)

REQUEST_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    ["method", "endpoint"],
)

ACTIVE_USERS = Gauge(
    "mimo_active_users",
    "Number of authenticated users with active sessions",
)

TAX_CALCULATIONS = Counter(
    "mimo_tax_calculations_total",
    "Total number of tax calculations performed",
    ["fiscal_year"],
)

AI_RECOMMENDATIONS = Counter(
    "mimo_ai_recommendations_total",
    "Total number of AI recommendations generated",
    ["provider", "status"],
)

RATE_LIMIT_HITS = Counter(
    "mimo_rate_limit_hits_total",
    "Total number of rate limit hits",
    ["endpoint"],
)

DATABASE_QUERIES = Counter(
    "mimo_database_queries_total",
    "Total number of database queries",
    ["operation"],
)

DATABASE_ERRORS = Counter(
    "mimo_database_errors_total",
    "Total number of database errors",
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect Prometheus metrics for HTTP requests.

    Tracks:
    - Request count by method, endpoint, status
    - Request duration (latency) by method, endpoint
    - Requests in progress
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics endpoint to avoid infinite loop
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = self._get_endpoint(request)

        # Track requests in progress
        REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).inc()

        start_time = time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # Record metrics
            duration = time() - start_time

            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()

            REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            REQUEST_IN_PROGRESS.labels(method=method, endpoint=endpoint).dec()

        return response

    def _get_endpoint(self, request: Request) -> str:
        """
        Extract endpoint path, normalizing dynamic segments.

        Examples:
            /api/calculate -> /api/calculate
            /auth/callback?code=... -> /auth/callback
        """
        path = request.url.path

        # Normalize common patterns
        if path.startswith("/api/"):
            return path.split("?")[0]
        if path.startswith("/auth/"):
            return path.split("?")[0]
        if path.startswith("/calculator"):
            return "/calculator"

        return path
