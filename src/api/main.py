from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from src.api.v1.routers import (
    tax_router,
    recommendations_router,
    multi_agent_router,
    auth_router,
)
from src.infrastructure.config.settings import get_settings
from src.api.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
    log_requests_middleware,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    from src.infrastructure.persistence.sqlite_usage_repository import (
        SqliteUsageRepository,
    )

    settings = get_settings()
    _ = SqliteUsageRepository(settings.database_url)
    # Database is auto-initialized in repository constructor

    yield

    # Shutdown: cleanup if needed
    pass


def create_app() -> FastAPI:
    """
    Factory function to create FastAPI application.
    Centralizes app configuration and setup.
    """
    settings = get_settings()

    app = FastAPI(
        title="Mimo - Calculadora Fiscal",
        description="Mexican Tax Calculator for Individuals",
        version="0.2.0",
        lifespan=lifespan,
    )

    # Add exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Add middlewares
    app.middleware("http")(log_requests_middleware)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    # Include routers
    app.include_router(auth_router.router)
    app.include_router(tax_router.router)
    app.include_router(recommendations_router.router)
    app.include_router(multi_agent_router.router)

    # Root redirect
    @app.get("/")
    async def read_root():
        """Redirects the root path to the calculator page"""
        return RedirectResponse(url="/calculator", status_code=302)

    return app


# Create app instance
app = create_app()

# Templates (keeping backward compatibility)
templates = Jinja2Templates(directory="templates")


# Keep old calculator endpoint for backward compatibility
async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current user from session"""
    user = request.session.get("user")
    if user:
        return user
    return None


@app.get("/calculator", response_class=HTMLResponse)
async def calculator_page(request: Request):
    """Render calculator page"""
    user = await get_current_user(request)
    return templates.TemplateResponse(
        "calculator.html", {"request": request, "user": user}
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
