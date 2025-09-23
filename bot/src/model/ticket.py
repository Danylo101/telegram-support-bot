from datetime import datetime, timezone
from typing import Optional, List

from pydantic import BaseModel, Field


class Ticket(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: int
    description: str
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    comments: List[str] = []
