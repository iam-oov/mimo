"""
Domain exceptions for Mimo Tax Calculator.

This module defines a hierarchy of domain-specific exceptions that provide
clear error categorization without exposing internal details to users.
"""


class MimoException(Exception):
    """
    Base exception for all Mimo errors.

    All domain-specific exceptions should inherit from this class.
    """

    def __init__(self, message: str, internal_details: str | None = None):
        """
        Initialize MimoException.

        Args:
            message: User-friendly error message (safe to expose to clients)
            internal_details: Technical details for logging (NOT exposed to clients)
        """
        super().__init__(message)
        self.message = message
        self.internal_details = internal_details

    def __str__(self) -> str:
        return self.message


class TaxCalculationError(MimoException):
    """
    Tax calculation domain errors.

    Raised when tax calculation fails due to:
    - Invalid input data (negative income, invalid percentages)
    - Business rule violations (deductions exceeding limits)
    - ISR table lookup failures
    """

    pass


class ValidationError(MimoException):
    """
    Input validation errors.

    Raised when user input fails validation:
    - Missing required fields
    - Invalid data types
    - Out-of-range values
    """

    pass


class AIProviderError(MimoException):
    """
    AI provider errors.

    Raised when AI recommendation or multi-agent analysis fails:
    - API key invalid or missing
    - Provider service unavailable
    - Rate limit exceeded on provider side
    - Malformed AI response
    """

    pass


class AIProviderUnavailableError(AIProviderError):
    """
    AI provider is unavailable.

    Raised when no AI provider is configured or all providers are down.
    System should fall back to static recommendations.
    """

    pass


class RateLimitExceededError(MimoException):
    """
    Rate limit exceeded.

    Raised when user exceeds their daily limit for:
    - AI recommendations
    - Multi-agent analysis
    - Chat messages
    """

    def __init__(
        self,
        message: str,
        usage_count: int,
        daily_limit: int,
        internal_details: str | None = None,
    ):
        super().__init__(message, internal_details)
        self.usage_count = usage_count
        self.daily_limit = daily_limit


class AuthenticationError(MimoException):
    """
    Authentication errors.

    Raised when:
    - User is not logged in
    - Session expired
    - OAuth callback failed
    """

    pass


class AuthorizationError(MimoException):
    """
    Authorization errors.

    Raised when:
    - User doesn't have permission for an action
    - Resource access denied
    """

    pass


class ConfigurationError(MimoException):
    """
    Configuration errors.

    Raised when:
    - Required environment variables missing
    - Invalid API keys
    - Startup validation failures
    """

    pass


class DatabaseError(MimoException):
    """
    Database operation errors.

    Raised when:
    - Database connection fails
    - Query execution fails
    - Data integrity violations
    """

    pass


class MemoryStoreError(MimoException):
    """
    Memory/Vector store errors.

    Raised when:
    - Conversation storage fails
    - Vector store operations fail
    - Memory cleanup errors
    """

    pass
