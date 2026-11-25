"""Database models. Importing this package registers every table on Base.metadata."""

from app.models.analysis import Analysis
from app.models.base import Base
from app.models.location import City, Neighborhood
from app.models.property import Property
from app.models.supabase_auth import auth_users_table
from app.models.user_profile import UserProfile

__all__ = [
    "Analysis",
    "Base",
    "City",
    "Neighborhood",
    "Property",
    "UserProfile",
    "auth_users_table",
]
