from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List

from bson import ObjectId
from pydantic import BaseModel, Field, ConfigDict


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, *args, **kwargs):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        schema.update(type="string")
        return schema


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    AWAITING_USER = "awaiting_user"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserRole(str, Enum):
    CLIENT = "client"
    AGENT = "agent"
    ADMIN = "admin"


class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_tg_id: Optional[int] = None
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole = UserRole.CLIENT
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class Category(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str
    description: Optional[str] = None
    parent_category_id: Optional[PyObjectId] = None


class Attachment(BaseModel):
    file_unique_id: str
    file_id: str
    mime_type: str
    uploaded_by: PyObjectId
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InternalNote(BaseModel):
    author_id: PyObjectId  # ID агента або адміна
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Message(BaseModel):
    author_id: PyObjectId
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_from_support: bool = False
    attachments: List[Attachment] = []


class Ticket(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ticket_seq_id: int
    title: str
    user_id: PyObjectId

    category_id: Optional[PyObjectId] = None
    tags: List[str] = []

    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM

    sla_due_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    history: List[Message] = []
    internal_notes: List[InternalNote] = []

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class KnowledgeBaseArticle(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    title: str
    content: str
    category_id: PyObjectId
    author_id: PyObjectId
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = []
    is_published: bool = True


class Feedback(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    ticket_id: PyObjectId
    user_id: PyObjectId
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
