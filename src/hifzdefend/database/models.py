"""Database models for customer portal."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .engine import Base


class Ticket(Base):
    """Support ticket model."""

    __tablename__ = "tickets"

    id = Column(String(50), primary_key=True, index=True)  # TKT-YYYYMMDD-XXXX
    user_id = Column(String(100), nullable=False, index=True)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        Enum("technical", "billing", "feature_request", "other", name="ticket_category"),
        nullable=False,
        default="technical",
    )
    priority = Column(
        Enum("low", "medium", "high", "urgent", name="ticket_priority"),
        nullable=False,
        default="medium",
    )
    status = Column(
        Enum("open", "in_progress", "resolved", "closed", name="ticket_status"),
        nullable=False,
        default="open",
    )
    assigned_to = Column(String(100), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_viewed_at = Column(DateTime, nullable=True)

    # Relationships
    replies = relationship("TicketReply", back_populates="ticket", cascade="all, delete-orphan")


class TicketReply(Base):
    """Ticket reply/comment model."""

    __tablename__ = "ticket_replies"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    attachments = Column(Text, nullable=True)  # JSON string of attachment URLs
    is_internal = Column(Boolean, default=False, nullable=False)  # Internal notes vs customer-facing
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="replies")


class AdminLog(Base):
    """Admin action audit log."""

    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String(100), nullable=False, index=True)
    action = Column(
        Enum(
            "license_created",
            "license_revoked",
            "license_extended",
            "ticket_assigned",
            "ticket_closed",
            "ticket_status_changed",
            "ticket_priority_changed",
            "user_created",
            "user_disabled",
            name="admin_action_type",
        ),
        nullable=False,
    )
    resource_type = Column(String(50), nullable=False)  # "license", "ticket", "user"
    resource_id = Column(String(100), nullable=False, index=True)
    details = Column(Text, nullable=True)  # JSON string with additional details
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class DiscountCode(Base):
    """Discount code for purchases."""

    __tablename__ = "discount_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    type = Column(
        Enum("percentage", "fixed_amount", "trial_extension", name="discount_type"),
        nullable=False,
    )
    value = Column(Float, nullable=False)  # Percentage (0-100) or dollar amount
    expiration = Column(DateTime, nullable=True)
    usage_limit = Column(Integer, nullable=True)  # Max number of uses
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
