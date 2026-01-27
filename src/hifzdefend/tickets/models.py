"""Pydantic models for support tickets."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TicketCategory(str, Enum):
    """Ticket category enum."""

    TECHNICAL = "technical"
    BILLING = "billing"
    FEATURE_REQUEST = "feature_request"
    OTHER = "other"


class TicketPriority(str, Enum):
    """Ticket priority enum."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketStatus(str, Enum):
    """Ticket status enum."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketReplyCreate(BaseModel):
    """Create a reply to a ticket."""

    message: str = Field(..., min_length=10, max_length=5000)
    attachments: Optional[List[str]] = None
    is_internal: bool = False

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v


class TicketReply(BaseModel):
    """Ticket reply model."""

    id: int
    ticket_id: str
    user_id: str
    message: str
    attachments: Optional[List[str]] = None
    is_internal: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class TicketCreate(BaseModel):
    """Create a new support ticket."""

    subject: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    category: TicketCategory = TicketCategory.TECHNICAL
    priority: TicketPriority = TicketPriority.MEDIUM
    attachments: Optional[List[str]] = None

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Subject cannot be empty or whitespace only")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Validate description is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v


class TicketUpdate(BaseModel):
    """Update ticket status or priority."""

    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_to: Optional[str] = None


class Ticket(BaseModel):
    """Support ticket model."""

    id: str
    user_id: str
    subject: str
    description: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    assigned_to: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_viewed_at: Optional[datetime] = None
    reply_count: int = 0
    last_reply_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
    }


class TicketWithReplies(Ticket):
    """Ticket with full conversation history."""

    replies: List[TicketReply] = []

    model_config = {
        "from_attributes": True,
    }
