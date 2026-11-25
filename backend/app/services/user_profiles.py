"""Creation and retrieval of the application profile for a signed-in user."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth.token_verifier import AuthenticatedUser
from app.models import UserProfile


def get_or_create_profile(session: Session, user: AuthenticatedUser) -> UserProfile:
    """Return the user's profile, creating it on the first authenticated request.

    The insert ignores an existing row, so two simultaneous first requests cannot create
    duplicates or fail. An existing profile is never overwritten by token data.
    """
    insert_if_missing = (
        insert(UserProfile)
        .values(
            user_id=user.user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        .on_conflict_do_nothing(index_elements=[UserProfile.user_id])
    )
    session.execute(insert_if_missing)
    session.commit()

    return session.scalars(select(UserProfile).where(UserProfile.user_id == user.user_id)).one()
