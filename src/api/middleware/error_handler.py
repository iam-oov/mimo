"""
Centralized error handling middleware.
Provides consistent error responses across all API endpoints.
"""

import logging
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standardized error response format."""

    def __init__(
        self, error: str, message: str, status_code: int, details: dict | None = None
    ):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON response."""
        response = {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            response["details"] = self.details
        return response


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle HTTP exceptions (4xx, 5xx errors).

    Args:
        request: FastAPI request
        exc: HTTP exception

    Returns:
        JSON response with error details
    """
    error_type = _get_error_type(exc.status_code)

    # Log error for monitoring
    if exc.status_code >= 500:
        logger.error(
            f"Server error: {exc.status_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
            },
        )
    else:
        logger.warning(
            f"Client error: {exc.status_code} - {exc.detail}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
            },
        )

    error_response = ErrorResponse(
        error=error_type,
        message=str(exc.detail),
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors (422 Unprocessable Entity).

    Args:
        request: FastAPI request
        exc: Validation error

    Returns:
        JSON response with validation error details
    """
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )

    # Format validation errors for better readability
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {
                "field": field,
                "message": error["msg"],
                "type": error["type"],
            }
        )

    error_response = ErrorResponse(
        error="validation_error",
        message="Invalid request data",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": formatted_errors},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict(),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions (500 Internal Server Error).

    Args:
        request: FastAPI request
        exc: Any exception

    Returns:
        JSON response with generic error message
    """
    logger.exception(
        f"Unexpected error: {type(exc).__name__} - {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
        exc_info=exc,
    )

    error_response = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred. Please try again later.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details={
            "exception_type": type(exc).__name__,
        }
        if logger.level <= logging.DEBUG
        else {},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict(),
    )


def _get_error_type(status_code: int) -> str:
    """
    Get error type string based on status code.

    Args:
        status_code: HTTP status code

    Returns:
        Error type identifier
    """
    error_types = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_server_error",
        502: "bad_gateway",
        503: "service_unavailable",
        504: "gateway_timeout",
    }

    return error_types.get(status_code, f"http_{status_code}")


async def log_requests_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to log all incoming requests and responses.

    Args:
        request: FastAPI request
        call_next: Next middleware/handler

    Returns:
        Response from next handler
    """
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
        },
    )

    return response
