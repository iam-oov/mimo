"""
Authentication router.
Handles OAuth login, callback, and logout endpoints.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from src.auth.infrastructure.dependencies import (
    get_current_user_optional,
    get_oauth_service,
)
from src.auth.infrastructure.oauth_service import GoogleOAuthService
from src.shared.domain.exceptions import AuthenticationError
from src.shared.infrastructure.logging.structured_logger import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)


@router.get("/google")
async def login_with_google(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
):
    """
    Initiate Google OAuth 2.0 login flow.

    Redirects user to Google's authorization page where they can sign in with their Google account.
    After successful authentication, Google redirects back to /auth/callback with an authorization code.

    **OAuth Scopes Requested:**
    - openid: OpenID Connect authentication
    - email: User's email address
    - profile: User's basic profile info (name, picture)

    Args:
        request: FastAPI request (used to determine redirect URI)
        oauth_service: Google OAuth service instance (injected)

    Returns:
        RedirectResponse to Google OAuth consent screen

    Example Flow:
        1. User clicks "Iniciar Sesión con Google"
        2. GET /auth/google
        3. Redirect to accounts.google.com/o/oauth2/auth
        4. User signs in with Google
        5. Google redirects to /auth/callback?code=...
    """
    authorization_url = oauth_service.get_authorization_url(request)
    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
):
    """
    Handle Google OAuth callback.
    Exchanges authorization code for tokens and stores user in session.

    Args:
        request: FastAPI request
        code: Authorization code from Google
        oauth_service: OAuth service instance

    Returns:
        Redirect to calculator page on success

    Raises:
        HTTPException: 400 if authentication fails
    """
    try:
        # Complete authentication flow
        user = oauth_service.authenticate_user(request, code)

        # Store user in session
        oauth_service.store_user_in_session(request, user)

        # Redirect to calculator
        return RedirectResponse(url="/calculator", status_code=302)

    except AuthenticationError as e:
        logger.warning(
            "Authentication failed",
            error_message=e.message,
            internal_details=e.internal_details,
        )
        raise HTTPException(
            status_code=400,
            detail="Error de autenticación. Por favor intenta de nuevo.",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error during authentication")
        raise HTTPException(
            status_code=400,
            detail="Error de autenticación. Por favor intenta de nuevo.",
        )


@router.get("/logout")
async def logout(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
):
    """
    Log out the current user and clear session.

    Clears the user's session data (Google OAuth tokens, user info) from SessionMiddleware
    and redirects back to the calculator page. After logout, user will need to authenticate
    again to use AI-powered features (recommendations, multi-agent analysis).

    Args:
        request: FastAPI request with session
        oauth_service: Google OAuth service instance (injected)

    Returns:
        RedirectResponse to /calculator with 302 status

    Note:
        Does NOT revoke tokens on Google's side, only clears local session.
    """
    oauth_service.clear_session(request)
    return RedirectResponse(url="/calculator", status_code=302)


@router.get("/status")
async def auth_status(
    user: dict[str, Any] | None = Depends(get_current_user_optional),
):
    """
    Check current authentication status.

    Returns authentication state and user information if logged in. Used by frontend
    to determine whether to show "Iniciar Sesión" or user profile, and to conditionally
    enable AI features that require authentication.

    Args:
        user: Current user from session (None if not authenticated, injected)

    Returns:
        JSON with authentication status:
        - If authenticated: `{"authenticated": true, "user": {"name": "...", "email": "..."}}`
        - If not authenticated: `{"authenticated": false, "user": null}`

    Example Response (Authenticated):
        ```json
        {
          "authenticated": true,
          "user": {
            "name": "Juan Pérez",
            "email": "juan@example.com"
          }
        }
        ```
    """
    if user:
        return {
            "authenticated": True,
            "user": {
                "name": user.get("name"),
                "email": user.get("email"),
            },
        }
    else:
        return {"authenticated": False, "user": None}
