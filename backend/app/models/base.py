"""Declarative base shared by all EstateAI database models."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# A fixed naming convention gives every constraint a predictable name, which keeps
# Alembic migrations reproducible and makes constraint errors easy to trace.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
