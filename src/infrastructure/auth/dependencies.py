"""
Authentication dependencies for FastAPI.
Provides reusable dependencies for auth checks and user retrieval.
"""

from typing import Dict, Any
from functools import lru_cache

from fastapi import Request, HTTPException, Depends

from src.infrastructure.config.settings import get_settings
from src.infrastructure.auth.oauth_service import GoogleOAuthService


@lru_cache
def get_oauth_service() -> GoogleOAuthService:
    """Get singleton OAuth service instance."""
    settings = get_settings()
    return GoogleOAuthService(settings)


def get_current_user_optional(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
) -> Dict[str, Any] | None:
    """
    Get current authenticated user from session (optional).
    Returns None if user is not authenticated.

    Use this when authentication is optional for an endpoint.

    Args:
        request: FastAPI request object
        oauth_service: OAuth service instance

    Returns:
        User dict if authenticated, None otherwise
    """
    return oauth_service.get_user_from_session(request)


def get_current_user(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
) -> Dict[str, Any]:
    """
    Get current authenticated user from session (required).
    Raises 401 if user is not authenticated.

    Use this as a dependency for protected endpoints.

    Args:
        request: FastAPI request object
        oauth_service: OAuth service instance

    Returns:
        User dict with 'sub', 'email', 'name'

    Raises:
        HTTPException: 401 if user is not authenticated
    """
    user = oauth_service.get_user_from_session(request)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please login with Google.",
        )

    return user


def get_user_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Extract user ID from authenticated user.
    User ID is Google's 'sub' claim, falling back to email.

    Args:
        user: Authenticated user dict

    Returns:
        User identifier string
    """
    return user.get("sub") or user.get("email", "")
