"""Endpoints about the signed-in user."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db_session
from app.schemas.user_profile import UserProfileResponse
from app.services.user_profiles import get_or_create_profile

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def read_current_user_profile(
    current_user: CurrentUser,
    session: Annotated[Session, Depends(get_db_session)],
) -> UserProfileResponse:
    """Return the signed-in user's profile, creating it on first sign-in."""
    profile = get_or_create_profile(session, current_user)
    return UserProfileResponse.model_validate(profile)
