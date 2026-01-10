"""
Centralized error handling middleware.
Provides consistent error responses across all API endpoints.
"""

from collections.abc import Callable

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.shared.domain.exceptions import (
    AIProviderError,
    AIProviderUnavailableError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    MemoryStoreError,
    MimoException,
    RateLimitExceededError,
    TaxCalculationError,
    ValidationError,
)
from src.shared.infrastructure.logging.structured_logger import get_logger

logger = get_logger(__name__)


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
            "Server error",
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=str(exc.detail),
        )
    else:
        logger.warning(
            "Client error",
            path=request.url.path,
            method=request.method,
            status_code=exc.status_code,
            detail=str(exc.detail),
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

    logger.warning(
        "Validation error",
        path=request.url.path,
        method=request.method,
        error_count=len(formatted_errors),
        errors=formatted_errors,
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
    Also handles domain-specific exceptions with appropriate status codes.

    Args:
        request: FastAPI request
        exc: Any exception

    Returns:
        JSON response with appropriate error message
    """
    # Handle domain-specific exceptions
    if isinstance(exc, RateLimitExceededError):
        logger.warning(
            "Rate limit exceeded",
            path=request.url.path,
            user_id=getattr(exc, "usage_count", None),
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponse(
                error="rate_limit_exceeded",
                message=exc.message,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                details={
                    "usage_count": exc.usage_count,
                    "daily_limit": exc.daily_limit,
                },
            ).to_dict(),
        )

    if isinstance(exc, ValidationError):
        logger.warning(
            "Validation error",
            path=request.url.path,
            message=exc.message,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="validation_error",
                message=exc.message,
                status_code=status.HTTP_400_BAD_REQUEST,
            ).to_dict(),
        )

    if isinstance(exc, TaxCalculationError):
        logger.error(
            "Tax calculation error",
            path=request.url.path,
            message=exc.message,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error="tax_calculation_error",
                message="Error al calcular impuestos. Por favor verifica tus datos.",
                status_code=status.HTTP_400_BAD_REQUEST,
            ).to_dict(),
        )

    if isinstance(exc, (AuthenticationError, AuthorizationError)):
        logger.warning(
            "Authentication/Authorization error",
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        status_code = (
            status.HTTP_401_UNAUTHORIZED
            if isinstance(exc, AuthenticationError)
            else status.HTTP_403_FORBIDDEN
        )
        return JSONResponse(
            status_code=status_code,
            content=ErrorResponse(
                error="authentication_error"
                if isinstance(exc, AuthenticationError)
                else "authorization_error",
                message=exc.message,
                status_code=status_code,
            ).to_dict(),
        )

    if isinstance(exc, AIProviderUnavailableError):
        logger.error(
            "AI provider unavailable",
            path=request.url.path,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="service_unavailable",
                message="El servicio de IA no está disponible. Intenta más tarde.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ).to_dict(),
        )

    if isinstance(exc, AIProviderError):
        logger.error(
            "AI provider error",
            path=request.url.path,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                error="ai_provider_error",
                message="Error en el servicio de IA. Intenta más tarde.",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            ).to_dict(),
        )

    if isinstance(exc, (DatabaseError, MemoryStoreError)):
        logger.error(
            "Storage error",
            path=request.url.path,
            error_type=type(exc).__name__,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="storage_error",
                message="Error de almacenamiento. Nuestro equipo ha sido notificado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).to_dict(),
        )

    if isinstance(exc, ConfigurationError):
        logger.critical(
            "Configuration error",
            path=request.url.path,
            message=exc.message,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="configuration_error",
                message="Error de configuración. Nuestro equipo ha sido notificado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).to_dict(),
        )

    if isinstance(exc, MimoException):
        logger.error(
            "Mimo domain error",
            path=request.url.path,
            error_type=type(exc).__name__,
            message=exc.message,
            internal_details=exc.internal_details,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="domain_error",
                message="Error en el sistema. Nuestro equipo ha sido notificado.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ).to_dict(),
        )

    # Handle truly unexpected exceptions
    logger.exception(
        "Unexpected error",
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )

    error_response = ErrorResponse(
        error="internal_server_error",
        message="Error inesperado. Por favor intenta de nuevo más tarde.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
        "Incoming request",
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
        client_host=request.client.host if request.client else None,
    )

    # Process request
    response = await call_next(request)

    # Log response
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )

    return response
