"""API endpoints for support tickets."""

import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...auth.manager import AuthManager
from ...auth.tokens import TokenManager
from ...database import TicketReply as DBTicketReply
from ...database import Ticket as DBTicket
from ...database.engine import get_db
from ...tickets.models import (
    Ticket,
    TicketCreate,
    TicketReply,
    TicketReplyCreate,
    TicketStatus,
    TicketWithReplies,
)

router = APIRouter(prefix="/tickets", tags=["tickets"])

auth_manager = AuthManager()
token_manager = TokenManager()


def get_current_user_id(token: str) -> str:
    """Extract user ID from JWT token.

    Args:
        token: JWT access token

    Returns:
        User ID

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = token_manager.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def generate_ticket_id() -> str:
    """Generate unique ticket ID in format TKT-YYYYMMDD-XXXX.

    Returns:
        Ticket ID
    """
    import random

    date_str = datetime.utcnow().strftime("%Y%m%d")
    random_suffix = f"{random.randint(0, 9999):04d}"
    return f"TKT-{date_str}-{random_suffix}"


@router.post("/", response_model=Ticket, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Create a new support ticket.

    Args:
        ticket_data: Ticket creation data
        token: JWT access token
        db: Database session

    Returns:
        Created ticket

    Raises:
        HTTPException: If creation fails
    """
    user_id = get_current_user_id(token)

    # Generate unique ticket ID
    ticket_id = generate_ticket_id()

    # Create ticket
    db_ticket = DBTicket(
        id=ticket_id,
        user_id=user_id,
        subject=ticket_data.subject,
        description=ticket_data.description,
        category=ticket_data.category.value,
        priority=ticket_data.priority.value,
        status=TicketStatus.OPEN.value,
    )

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)

    # Convert to response model
    ticket = Ticket.model_validate(db_ticket)
    ticket.reply_count = 0
    ticket.last_reply_at = None

    # TODO: Send email confirmation to user

    return ticket


@router.get("/", response_model=List[Ticket])
async def list_tickets(
    token: str = Query(..., description="JWT access token"),
    status_filter: Optional[str] = Query(None, description="Filter by status (comma-separated)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """List all tickets for the current user.

    Args:
        token: JWT access token
        status_filter: Optional status filter
        category: Optional category filter
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        List of tickets

    Raises:
        HTTPException: If retrieval fails
    """
    user_id = get_current_user_id(token)

    # Build query
    query = db.query(DBTicket).filter(DBTicket.user_id == user_id)

    # Apply filters
    if status_filter:
        statuses = [s.strip() for s in status_filter.split(",")]
        query = query.filter(DBTicket.status.in_(statuses))

    if category:
        query = query.filter(DBTicket.category == category)

    # Order by created date (newest first)
    query = query.order_by(DBTicket.created_at.desc())

    # Pagination
    offset = (page - 1) * page_size
    db_tickets = query.offset(offset).limit(page_size).all()

    # Convert to response models with reply counts
    tickets = []
    for db_ticket in db_tickets:
        ticket = Ticket.model_validate(db_ticket)

        # Get reply count and last reply time
        reply_count = db.query(DBTicketReply).filter(
            DBTicketReply.ticket_id == db_ticket.id,
            DBTicketReply.is_internal == False,
        ).count()

        last_reply = db.query(DBTicketReply).filter(
            DBTicketReply.ticket_id == db_ticket.id
        ).order_by(DBTicketReply.created_at.desc()).first()

        ticket.reply_count = reply_count
        ticket.last_reply_at = last_reply.created_at if last_reply else None

        tickets.append(ticket)

    return tickets


@router.get("/{ticket_id}", response_model=TicketWithReplies)
async def get_ticket(
    ticket_id: str,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Get ticket details with full conversation history.

    Args:
        ticket_id: Ticket ID
        token: JWT access token
        db: Database session

    Returns:
        Ticket with replies

    Raises:
        HTTPException: If ticket not found or access denied
    """
    user_id = get_current_user_id(token)

    # Get ticket
    db_ticket = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Verify ownership
    if db_ticket.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Mark as viewed
    db_ticket.last_viewed_at = datetime.utcnow()
    db.commit()

    # Get all non-internal replies
    db_replies = db.query(DBTicketReply).filter(
        DBTicketReply.ticket_id == ticket_id,
        DBTicketReply.is_internal == False,
    ).order_by(DBTicketReply.created_at.asc()).all()

    # Convert to response model
    ticket = TicketWithReplies.model_validate(db_ticket)
    ticket.replies = [TicketReply.model_validate(r) for r in db_replies]
    ticket.reply_count = len(db_replies)
    ticket.last_reply_at = db_replies[-1].created_at if db_replies else None

    return ticket


@router.post("/{ticket_id}/replies", response_model=TicketReply, status_code=status.HTTP_201_CREATED)
async def create_reply(
    ticket_id: str,
    reply_data: TicketReplyCreate,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Add a reply to a ticket.

    Args:
        ticket_id: Ticket ID
        reply_data: Reply data
        token: JWT access token
        db: Database session

    Returns:
        Created reply

    Raises:
        HTTPException: If ticket not found or access denied
    """
    user_id = get_current_user_id(token)

    # Get ticket
    db_ticket = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Verify ownership
    if db_ticket.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Create reply
    attachments_json = json.dumps(reply_data.attachments) if reply_data.attachments else None

    db_reply = DBTicketReply(
        ticket_id=ticket_id,
        user_id=user_id,
        message=reply_data.message,
        attachments=attachments_json,
        is_internal=False,  # Customer replies are never internal
    )

    db.add(db_reply)

    # Update ticket status if it was resolved/closed
    if db_ticket.status in [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]:
        db_ticket.status = TicketStatus.OPEN.value

    # Update ticket updated_at
    db_ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_reply)

    # TODO: Send email notification to assigned support agent

    return TicketReply.model_validate(db_reply)
