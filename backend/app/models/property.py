"""Physical characteristics of a residential property."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

PROPERTY_TYPES = ("apartment", "house")


class Property(Base):
    """A property described by its characteristics, independent of any listing price.

    Optional characteristics use NULL for "unknown". For the boolean amenities, NULL means
    the information was not provided, while FALSE means the seller stated it is absent.
    """

    __tablename__ = "property"
    __table_args__ = (
        CheckConstraint(f"property_type IN {PROPERTY_TYPES}", name="property_type_allowed"),
        CheckConstraint("usable_area_m2 > 0", name="usable_area_positive"),
        CheckConstraint("rooms >= 1", name="rooms_positive"),
        CheckConstraint("total_floors IS NULL OR total_floors >= 1", name="total_floors_positive"),
        # The apartment floor does not apply to a house, so a house never stores one.
        # For an apartment, a NULL floor means the floor is unknown.
        CheckConstraint(
            "property_type <> 'house' OR floor IS NULL", name="house_has_no_apartment_floor"
        ),
        CheckConstraint(
            "floor IS NULL OR total_floors IS NULL OR floor <= total_floors",
            name="floor_within_building",
        ),
        CheckConstraint(
            "construction_year IS NULL OR construction_year >= 1800",
            name="construction_year_plausible",
        ),
    )

    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    neighborhood_id: Mapped[int] = mapped_column(
        ForeignKey("neighborhood.neighborhood_id", ondelete="RESTRICT")
    )
    property_type: Mapped[str] = mapped_column(String(30))
    usable_area_m2: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    rooms: Mapped[int] = mapped_column(SmallInteger)
    floor: Mapped[int | None] = mapped_column(SmallInteger)
    total_floors: Mapped[int | None] = mapped_column(SmallInteger)
    construction_year: Mapped[int | None] = mapped_column(SmallInteger)
    condition: Mapped[str | None] = mapped_column(String(30))
    has_balcony: Mapped[bool | None] = mapped_column(Boolean)
    has_elevator: Mapped[bool | None] = mapped_column(Boolean)
    has_parking: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
