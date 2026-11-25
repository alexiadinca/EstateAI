"""API response shapes for user profiles."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    registered_at: datetime
