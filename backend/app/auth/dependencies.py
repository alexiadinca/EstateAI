"""FastAPI dependencies that resolve the signed-in user from the Authorization header."""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.token_verifier import (
    AuthenticatedUser,
    AuthServiceUnavailableError,
    InvalidTokenError,
    SupabaseTokenVerifier,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# auto_error=False lets this module return a consistent 401 response for a missing token.
bearer_scheme = HTTPBearer(auto_error=False, description="Supabase access token")

_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


@lru_cache
def _create_project_verifier(supabase_url: str) -> SupabaseTokenVerifier:
    return SupabaseTokenVerifier.for_project(supabase_url)


def get_token_verifier() -> SupabaseTokenVerifier:
    supabase_url = get_settings().supabase_url
    if not supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured. Set SUPABASE_URL in backend/.env.",
        )
    return _create_project_verifier(supabase_url)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    verifier: Annotated[SupabaseTokenVerifier, Depends(get_token_verifier)],
) -> AuthenticatedUser:
    """Return the verified user. The user id always comes from the token, never the request."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to continue.",
            headers=_UNAUTHORIZED_HEADERS,
        )

    try:
        return verifier.verify(credentials.credentials)
    except InvalidTokenError as error:
        # The reason is logged for diagnosis; the token itself is never logged.
        logger.info("Rejected access token: %s", error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired. Sign in again.",
            headers=_UNAUTHORIZED_HEADERS,
        ) from error
    except AuthServiceUnavailableError as error:
        logger.warning("Supabase signing keys unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sign-in cannot be verified right now. Try again shortly.",
        ) from error


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
