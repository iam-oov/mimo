"""
Authentication router.
Handles OAuth login, callback, and logout endpoints.
"""

from typing import Dict, Any

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse

from src.infrastructure.auth.oauth_service import GoogleOAuthService
from src.infrastructure.auth.dependencies import (
    get_oauth_service,
    get_current_user_optional,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.get("/google")
async def login_with_google(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google's authorization page.

    Returns:
        Redirect to Google OAuth consent screen
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


@router.get("/logout")
async def logout(
    request: Request,
    oauth_service: GoogleOAuthService = Depends(get_oauth_service),
):
    """
    Log out the current user.
    Clears session and redirects to calculator.

    Returns:
        Redirect to calculator page
    """
    oauth_service.clear_session(request)
    return RedirectResponse(url="/calculator", status_code=302)


@router.get("/status")
async def auth_status(
    user: Dict[str, Any] | None = Depends(get_current_user_optional),
):
    """
    Check authentication status.
    Useful for frontend to determine if user is logged in.

    Returns:
        Dict with authenticated flag and user info if logged in
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
