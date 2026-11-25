"""Application profile linked one-to-one with a Supabase Auth user."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

USER_ROLES = ("user", "admin")


class UserProfile(Base):
    __tablename__ = "user_profile"
    __table_args__ = (CheckConstraint(f"role IN {USER_ROLES}", name="role_allowed"),)

    # Same identifier as auth.users.id. Passwords stay in Supabase Auth and are never copied here.
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True)
    # Names are optional until the sign-up form collects them; accounts created in the
    # Supabase dashboard have no names, and an empty string would hide that they are unknown.
    last_name: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(15), server_default=text("'user'"))
    extra_verification: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
