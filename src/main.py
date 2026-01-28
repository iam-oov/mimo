import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from src.auth.infrastructure.api.auth_router import router as auth_router
from src.recommendations.infrastructure.api.recommendations_router import (
    router as recommendations_router,
)
from src.shared.domain.constants.app_version import API_VERSION, APP_VERSION
from src.shared.infrastructure.api.middleware.error_handler import (
    generic_exception_handler,
    http_exception_handler,
    log_requests_middleware,
    validation_exception_handler,
)
from src.shared.infrastructure.api.middleware.metrics import PrometheusMiddleware
from src.shared.infrastructure.config.api_key_validator import validate_api_keys
from src.shared.infrastructure.config.settings import get_settings
from src.shared.infrastructure.health.health_check import HealthCheckService
from src.shared.infrastructure.logging.structured_logger import get_logger
from src.shared.infrastructure.persistence.postgres_usage_repository import (
    PostgresUsageRepository,
)
from src.tax_calculation.infrastructure.api.tax_router import router as tax_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    settings = get_settings()

    logger.info("🚀 Starting Mimo Tax Calculator...")

    # Initialize PostgreSQL database (required)
    if not settings.is_postgres:
        raise RuntimeError(
            "DATABASE_URL must be a PostgreSQL connection string. "
            "SQLite is no longer supported."
        )

    _ = PostgresUsageRepository(settings.database_url)
    logger.info("✅ PostgreSQL database initialized")

    # Validate API keys (fail fast if invalid)
    try:
        await validate_api_keys(settings)
        logger.info("✅ API keys validated")
    except Exception as e:
        logger.critical(
            "❌ API key validation failed - application will not start",
            error=str(e),
        )
        raise

    logger.info("✅ Mimo Tax Calculator started successfully")

    yield

    logger.info("👋 Shutting down Mimo Tax Calculator...")


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.
    Centralizes app configuration and setup.
    """
    settings = get_settings()

    app = FastAPI(
        title="Mimo - Calculadora Fiscal",
        description="Mexican Tax Calculator for Individuals",
        version=API_VERSION,
        lifespan=lifespan,
    )

    # Add exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Add middlewares (order matters: Prometheus → Logging → Session)
    app.add_middleware(PrometheusMiddleware)
    app.middleware("http")(log_requests_middleware)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    # Include routers
    app.include_router(auth_router)
    app.include_router(tax_router)
    app.include_router(recommendations_router)

    # Prometheus metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics"""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Health check endpoint for Railway
    @app.get("/health")
    async def health_check():
        """
        Health check endpoint with detailed component checks.
        Returns 200 if healthy, 503 if degraded.
        """
        import json

        settings = get_settings()
        health_service = HealthCheckService(settings)
        result = await health_service.check_all()

        status_code = 200 if result["status"] == "healthy" else 503
        return Response(
            content=json.dumps(result),
            status_code=status_code,
            media_type="application/json",
        )

    # Root redirect
    @app.get("/")
    async def read_root():
        """Redirects the root path to the calculator page"""
        return RedirectResponse(url="/calculator", status_code=302)

    return app


async def get_current_user(request: Request) -> dict[str, Any] | None:
    """Get current user from session"""
    user = request.session.get("user")
    if user:
        return user
    return None


app = create_app()
templates = Jinja2Templates(directory="templates")


@app.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    """Render calculator page"""

    user = await get_current_user(request)

    return templates.TemplateResponse(
        "calculator.html",
        {"request": request, "user": user, "version": APP_VERSION},
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
