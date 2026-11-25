"""Alembic migration environment for the EstateAI database."""

from logging.config import fileConfig

from alembic import context

from app.db.session import get_engine
from app.models import Base
from app.models.supabase_auth import SUPABASE_AUTH_SCHEMA

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def include_object(object_, name, type_, reflected, compare_to):
    """Keep Alembic away from tables owned by Supabase, such as auth.users."""
    if type_ == "table" and object_.schema == SUPABASE_AUTH_SCHEMA:
        return False
    return True


def run_migrations_offline() -> None:
    """Write the migration SQL to standard output instead of running it."""
    from app.core.config import get_settings

    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        include_object=include_object,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the database configured in backend/.env."""
    with get_engine().connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
