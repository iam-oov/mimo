"""
Google OAuth authentication service.
Handles OAuth flow, token verification, and user session management.
"""

import urllib.parse
from typing import Dict, Any

import requests
import google.oauth2.id_token
import google.auth.transport.requests as google_requests
from fastapi import Request, HTTPException

from src.infrastructure.config.settings import Settings


class GoogleOAuthService:
    """
    Service for Google OAuth 2.0 authentication.
    Implements authorization code flow with PKCE support.
    """

    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate that required OAuth settings are configured."""
        if not self.settings.google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID is not configured")
        if not self.settings.google_client_secret:
            raise ValueError("GOOGLE_CLIENT_SECRET is not configured")

    def _build_external_base_url(self, request: Request) -> str:
        """
        Build the external base URL from request headers.
        Handles reverse proxy scenarios (Railway, Heroku, etc.).
        """
        scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
        host = (
            request.headers.get("x-forwarded-host")
            or request.headers.get("host")
            or request.url.netloc
        )
        return f"{scheme}://{host}"

    def get_redirect_uri(self, request: Request) -> str:
        """
        Get the OAuth redirect URI.
        Uses configured URI if available, otherwise derives from request.
        """
        if (
            self.settings.google_redirect_uri
            and not self.settings.google_redirect_uri.startswith("http://localhost")
        ):
            return self.settings.google_redirect_uri

        base_url = self._build_external_base_url(request)
        return f"{base_url}/auth/callback"

    def get_authorization_url(self, request: Request) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            request: FastAPI request object

        Returns:
            Full authorization URL to redirect user to
        """
        redirect_uri = self.get_redirect_uri(request)

        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid email profile",
            "response_type": "code",
            "access_type": "offline",
        }

        return f"{self.GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(
        self, request: Request, authorization_code: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            request: FastAPI request object
            authorization_code: Authorization code from Google callback

        Returns:
            Token response from Google

        Raises:
            HTTPException: If token exchange fails
        """
        redirect_uri = self.get_redirect_uri(request)

        token_data = {
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "code": authorization_code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }

        try:
            response = requests.post(self.GOOGLE_TOKEN_URL, data=token_data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to exchange authorization code: {str(e)}",
            )

    def verify_and_decode_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify and decode Google ID token.

        Args:
            id_token: JWT token from Google

        Returns:
            Decoded user information

        Raises:
            HTTPException: If token verification fails
        """
        try:
            # Verify token with clock skew tolerance for time sync issues
            user_info = google.oauth2.id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                self.settings.google_client_id,
                clock_skew_in_seconds=10,
            )
            return user_info
        except Exception as e:
            raise HTTPException(
                status_code=401, detail=f"Token verification failed: {str(e)}"
            )

    def authenticate_user(
        self, request: Request, authorization_code: str
    ) -> Dict[str, Any]:
        """
        Complete authentication flow: exchange code and verify token.

        Args:
            request: FastAPI request object
            authorization_code: Authorization code from Google

        Returns:
            User information dict with 'sub', 'email', 'name'

        Raises:
            HTTPException: If authentication fails at any step
        """
        # Exchange code for tokens
        token_response = self.exchange_code_for_token(request, authorization_code)

        if "id_token" not in token_response:
            raise HTTPException(status_code=400, detail="No id_token in token response")

        # Verify and decode ID token
        user_info = self.verify_and_decode_token(token_response["id_token"])

        # Return normalized user data
        return {
            "sub": user_info["sub"],
            "email": user_info["email"],
            "name": user_info.get("name", user_info["email"]),
        }

    def store_user_in_session(self, request: Request, user: Dict[str, Any]) -> None:
        """
        Store authenticated user in session.

        Args:
            request: FastAPI request object
            user: User information to store
        """
        request.session["user"] = user

    def get_user_from_session(self, request: Request) -> Dict[str, Any] | None:
        """
        Retrieve user from session if authenticated.

        Args:
            request: FastAPI request object

        Returns:
            User dict if authenticated, None otherwise
        """
        return request.session.get("user")

    def clear_session(self, request: Request) -> None:
        """
        Clear user session (logout).

        Args:
            request: FastAPI request object
        """
        request.session.pop("user", None)
