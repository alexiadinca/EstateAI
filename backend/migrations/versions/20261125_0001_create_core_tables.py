"""Create the core tables for the Report 2 prototype.

Creates user_profile, city, neighborhood, property and analysis, following the relational
model in the project documentation. Tables for listings, extraction, ML models,
predictions and the personal workspace are added by later migrations.

Revision ID: 20261125_0001
Revises:
Create Date: 2026-11-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261125_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPLICATION_TABLES = ("user_profile", "city", "neighborhood", "property", "analysis")

# Cities covered by the regression dataset scope described in the ML presentation.
SUPPORTED_CITIES = [
    {"name": "Bucharest", "county": "Bucharest"},
    {"name": "Craiova", "county": "Dolj"},
]


def upgrade() -> None:
    op.create_table(
        "user_profile",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=15), server_default=sa.text("'user'"), nullable=False),
        sa.Column(
            "extra_verification", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("role IN ('user', 'admin')", name=op.f("ck_user_profile_role_allowed")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["auth.users.id"],
            name=op.f("fk_user_profile_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_user_profile")),
        sa.UniqueConstraint("email", name=op.f("uq_user_profile_email")),
    )

    city_table = op.create_table(
        "city",
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("county", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("city_id", name=op.f("pk_city")),
        sa.UniqueConstraint("name", "county", name="uq_city_name_county"),
    )

    op.create_table(
        "neighborhood",
        sa.Column("neighborhood_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(
            ["city_id"],
            ["city.city_id"],
            name=op.f("fk_neighborhood_city_id_city"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("neighborhood_id", name=op.f("pk_neighborhood")),
        sa.UniqueConstraint("city_id", "name", name="uq_neighborhood_city_id_name"),
    )

    op.create_table(
        "property",
        sa.Column(
            "property_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("neighborhood_id", sa.Integer(), nullable=False),
        sa.Column("property_type", sa.String(length=30), nullable=False),
        sa.Column("usable_area_m2", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("rooms", sa.SmallInteger(), nullable=False),
        sa.Column("floor", sa.SmallInteger(), nullable=True),
        sa.Column("total_floors", sa.SmallInteger(), nullable=True),
        sa.Column("construction_year", sa.SmallInteger(), nullable=True),
        sa.Column("structure", sa.String(length=30), nullable=True),
        sa.Column("condition", sa.String(length=30), nullable=True),
        sa.Column("has_balcony", sa.Boolean(), nullable=True),
        sa.Column("has_elevator", sa.Boolean(), nullable=True),
        sa.Column("has_parking", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "property_type IN ('apartment', 'house')",
            name=op.f("ck_property_property_type_allowed"),
        ),
        sa.CheckConstraint("usable_area_m2 > 0", name=op.f("ck_property_usable_area_positive")),
        sa.CheckConstraint("rooms >= 1", name=op.f("ck_property_rooms_positive")),
        sa.CheckConstraint(
            "total_floors IS NULL OR total_floors >= 1",
            name=op.f("ck_property_total_floors_positive"),
        ),
        sa.CheckConstraint(
            "property_type <> 'house' OR floor IS NULL",
            name=op.f("ck_property_house_has_no_apartment_floor"),
        ),
        sa.CheckConstraint(
            "floor IS NULL OR total_floors IS NULL OR floor <= total_floors",
            name=op.f("ck_property_floor_within_building"),
        ),
        sa.CheckConstraint(
            "construction_year IS NULL OR construction_year >= 1800",
            name=op.f("ck_property_construction_year_plausible"),
        ),
        sa.ForeignKeyConstraint(
            ["neighborhood_id"],
            ["neighborhood.neighborhood_id"],
            name=op.f("fk_property_neighborhood_id_neighborhood"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("property_id", name=op.f("pk_property")),
    )

    op.create_table(
        "analysis",
        sa.Column(
            "analysis_id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("property_id", sa.UUID(), nullable=False),
        sa.Column("confirmed_inputs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("asking_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column("asking_price_per_m2", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("status", sa.String(length=15), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'completed', 'unavailable', 'failed')",
            name=op.f("ck_analysis_status_allowed"),
        ),
        sa.CheckConstraint("asking_price > 0", name=op.f("ck_analysis_asking_price_positive")),
        sa.CheckConstraint(
            "asking_price_per_m2 > 0", name=op.f("ck_analysis_asking_price_per_m2_positive")
        ),
        sa.CheckConstraint("currency ~ '^[A-Z]{3}$'", name=op.f("ck_analysis_currency_iso_code")),
        sa.ForeignKeyConstraint(
            ["property_id"],
            ["property.property_id"],
            name=op.f("fk_analysis_property_id_property"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user_profile.user_id"],
            name=op.f("fk_analysis_user_id_user_profile"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("analysis_id", name=op.f("pk_analysis")),
    )
    op.create_index(
        "ix_analysis_user_id_created_at", "analysis", ["user_id", "created_at"], unique=False
    )
    op.create_index(op.f("ix_analysis_property_id"), "analysis", ["property_id"], unique=False)

    op.bulk_insert(city_table, SUPPORTED_CITIES)

    # Supabase exposes tables in the public schema through its Data API. Enabling Row Level
    # Security without any policy blocks all direct browser access, so every read and write
    # goes through FastAPI, which checks ownership. The backend connects as the table owner,
    # which is not restricted by these rules.
    for table_name in (*APPLICATION_TABLES, "alembic_version"):
        op.execute(f'ALTER TABLE public."{table_name}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_index(op.f("ix_analysis_property_id"), table_name="analysis")
    op.drop_index("ix_analysis_user_id_created_at", table_name="analysis")
    op.drop_table("analysis")
    op.drop_table("property")
    op.drop_table("neighborhood")
    op.drop_table("city")
    op.drop_table("user_profile")
