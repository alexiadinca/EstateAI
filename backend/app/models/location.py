"""Cities and neighborhoods used to locate properties."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class City(Base):
    __tablename__ = "city"
    __table_args__ = (UniqueConstraint("name", "county", name="uq_city_name_county"),)

    city_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    county: Mapped[str] = mapped_column(String(100))


class Neighborhood(Base):
    __tablename__ = "neighborhood"
    # The same neighborhood name may exist in two cities, but only once per city.
    __table_args__ = (UniqueConstraint("city_id", "name", name="uq_neighborhood_city_id_name"),)

    neighborhood_id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("city.city_id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(100))
