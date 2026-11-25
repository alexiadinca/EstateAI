"""Reference to the Supabase Auth users table.

Supabase manages auth.users itself. It is declared here only so that user_profile can
reference it with a foreign key. Alembic is configured to never create or modify it.
"""

from sqlalchemy import Column, Table
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

SUPABASE_AUTH_SCHEMA = "auth"

auth_users_table = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    schema=SUPABASE_AUTH_SCHEMA,
)
