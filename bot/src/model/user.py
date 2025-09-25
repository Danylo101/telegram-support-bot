from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone


class User(BaseModel):
    id: int
    name: Optional[str] = None
    phone: str
    role: str = "user"  # user | operator | admin
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))