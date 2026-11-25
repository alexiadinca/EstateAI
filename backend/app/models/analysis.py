"""Saved analysis snapshot of a property, owned by one user."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import CHAR, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# completed: a valuation was produced.
# unavailable: the property was saved, but no supported model could value it (reason stored).
# failed: an unexpected error occurred during valuation (message stored, retry allowed).
ANALYSIS_STATUSES = ("pending", "completed", "unavailable", "failed")


class Analysis(Base):
    """An immutable record of what the user confirmed and what was computed at that time.

    confirmed_inputs stores the reviewed property data as a snapshot, so reopening an
    analysis later shows the original inputs even if the property record changes.
    """

    __tablename__ = "analysis"
    __table_args__ = (
        CheckConstraint(f"status IN {ANALYSIS_STATUSES}", name="status_allowed"),
        CheckConstraint("asking_price > 0", name="asking_price_positive"),
        CheckConstraint("asking_price_per_m2 > 0", name="asking_price_per_m2_positive"),
        CheckConstraint("currency ~ '^[A-Z]{3}$'", name="currency_iso_code"),
        # Supports the "My analyses" list: one user's analyses, newest first.
        Index("ix_analysis_user_id_created_at", "user_id", "created_at"),
    )

    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # Ownership: every query for analyses is filtered by the authenticated user's id.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("user_profile.user_id", ondelete="CASCADE")
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("property.property_id", ondelete="RESTRICT"), index=True
    )
    confirmed_inputs: Mapped[dict[str, Any]] = mapped_column(JSONB)
    asking_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(CHAR(3))
    asking_price_per_m2: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(15))
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
