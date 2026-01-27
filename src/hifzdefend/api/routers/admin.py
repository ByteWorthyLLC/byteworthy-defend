"""API endpoints for admin operations."""

import json
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ...admin.models import (
    AdminAction,
    AdminActionType,
    AdminStats,
    LicenseExtend,
    LicenseRevoke,
    TicketAssignment,
)
from ...auth.manager import AuthManager
from ...auth.tokens import TokenManager
from ...database import AdminLog as DBAdminLog
from ...database import TicketReply as DBTicketReply
from ...database import Ticket as DBTicket
from ...database.engine import get_db
from ...tickets.models import Ticket, TicketReplyCreate, TicketStatus, TicketUpdate

router = APIRouter(prefix="/admin", tags=["admin"])

auth_manager = AuthManager()
token_manager = TokenManager()


def verify_admin_role(token: str) -> str:
    """Verify user has admin role.

    Args:
        token: JWT access token

    Returns:
        Admin user ID

    Raises:
        HTTPException: If user is not admin
    """
    try:
        payload = token_manager.decode_token(token)
        user_id = payload.get("sub")
        role = payload.get("role", "user")

        if role not in ["admin", "support"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or support access required",
            )

        return user_id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )


def log_admin_action(
    db: Session,
    admin_id: str,
    action: AdminActionType,
    resource_type: str,
    resource_id: str,
    details: Optional[dict] = None,
):
    """Log an admin action.

    Args:
        db: Database session
        admin_id: Admin user ID
        action: Action type
        resource_type: Resource type (license, ticket, user)
        resource_id: Resource ID
        details: Additional details
    """
    details_json = json.dumps(details) if details else None

    log_entry = DBAdminLog(
        admin_id=admin_id,
        action=action.value,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details_json,
    )

    db.add(log_entry)
    db.commit()


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Get admin dashboard statistics.

    Args:
        token: JWT access token
        db: Database session

    Returns:
        Admin statistics

    Raises:
        HTTPException: If access denied
    """
    verify_admin_role(token)

    # Calculate date ranges
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)

    # Get ticket statistics
    open_tickets = db.query(func.count(DBTicket.id)).filter(
        DBTicket.status.in_(["open", "in_progress"])
    ).scalar() or 0

    # Get tickets by priority
    tickets_by_priority = {}
    priority_counts = db.query(
        DBTicket.priority,
        func.count(DBTicket.id)
    ).filter(
        DBTicket.status.in_(["open", "in_progress"])
    ).group_by(DBTicket.priority).all()

    for priority, count in priority_counts:
        tickets_by_priority[priority] = count

    # TODO: Calculate customer, license, and subscription stats from auth/licensing modules
    # For now, return basic ticket statistics

    stats = AdminStats(
        total_customers=0,  # TODO: Implement
        total_licenses=0,  # TODO: Implement
        active_subscriptions=0,  # TODO: Implement
        mrr=0.0,  # TODO: Implement
        arr=0.0,  # TODO: Implement
        trial_conversion_rate=0.0,  # TODO: Implement
        open_tickets_count=open_tickets,
        tickets_by_priority=tickets_by_priority,
        recent_signups_7d=0,  # TODO: Implement
        recent_purchases_7d=0,  # TODO: Implement
        recent_revenue_7d=0.0,  # TODO: Implement
    )

    return stats


@router.get("/tickets", response_model=List[Ticket])
async def list_all_tickets(
    token: str = Query(..., description="JWT access token"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned agent"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all tickets (admin view).

    Args:
        token: JWT access token
        status_filter: Optional status filter
        priority: Optional priority filter
        assigned_to: Optional assigned agent filter
        page: Page number
        page_size: Items per page
        db: Database session

    Returns:
        List of all tickets

    Raises:
        HTTPException: If access denied
    """
    verify_admin_role(token)

    # Build query
    query = db.query(DBTicket)

    # Apply filters
    if status_filter:
        query = query.filter(DBTicket.status == status_filter)

    if priority:
        query = query.filter(DBTicket.priority == priority)

    if assigned_to:
        query = query.filter(DBTicket.assigned_to == assigned_to)

    # Order by priority (urgent first) then created date
    priority_order = {
        "urgent": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }

    # Get tickets and sort
    offset = (page - 1) * page_size
    db_tickets = query.offset(offset).limit(page_size).all()

    # Convert to response models
    tickets = []
    for db_ticket in db_tickets:
        ticket = Ticket.model_validate(db_ticket)

        # Get reply count
        reply_count = db.query(func.count(DBTicketReply.id)).filter(
            DBTicketReply.ticket_id == db_ticket.id
        ).scalar() or 0

        ticket.reply_count = reply_count

        tickets.append(ticket)

    # Sort by priority
    tickets.sort(key=lambda t: priority_order.get(t.priority.value, 99))

    return tickets


@router.put("/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assignment: TicketAssignment,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Assign ticket to an agent.

    Args:
        ticket_id: Ticket ID
        assignment: Assignment data
        token: JWT access token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If ticket not found or access denied
    """
    admin_id = verify_admin_role(token)

    # Get ticket
    db_ticket = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Update assignment
    db_ticket.assigned_to = assignment.agent_id
    db_ticket.updated_at = datetime.utcnow()

    db.commit()

    # Log action
    log_admin_action(
        db,
        admin_id,
        AdminActionType.TICKET_ASSIGNED,
        "ticket",
        ticket_id,
        {"agent_id": assignment.agent_id},
    )

    return {"message": "Ticket assigned successfully"}


@router.put("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: str,
    update: TicketUpdate,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Update ticket status or priority.

    Args:
        ticket_id: Ticket ID
        update: Update data
        token: JWT access token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If ticket not found or access denied
    """
    admin_id = verify_admin_role(token)

    # Get ticket
    db_ticket = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Update fields
    if update.status:
        db_ticket.status = update.status.value
        log_admin_action(
            db,
            admin_id,
            AdminActionType.TICKET_STATUS_CHANGED,
            "ticket",
            ticket_id,
            {"new_status": update.status.value},
        )

    if update.priority:
        db_ticket.priority = update.priority.value
        log_admin_action(
            db,
            admin_id,
            AdminActionType.TICKET_PRIORITY_CHANGED,
            "ticket",
            ticket_id,
            {"new_priority": update.priority.value},
        )

    if update.assigned_to is not None:
        db_ticket.assigned_to = update.assigned_to

    db_ticket.updated_at = datetime.utcnow()
    db.commit()

    # TODO: Send email to customer on status change (except internal notes)

    return {"message": "Ticket updated successfully"}


@router.post("/tickets/{ticket_id}/notes")
async def add_internal_note(
    ticket_id: str,
    note: TicketReplyCreate,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Add internal note to ticket (not visible to customer).

    Args:
        ticket_id: Ticket ID
        note: Note data
        token: JWT access token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If ticket not found or access denied
    """
    admin_id = verify_admin_role(token)

    # Get ticket
    db_ticket = db.query(DBTicket).filter(DBTicket.id == ticket_id).first()

    if not db_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # Create internal note
    attachments_json = json.dumps(note.attachments) if note.attachments else None

    db_reply = DBTicketReply(
        ticket_id=ticket_id,
        user_id=admin_id,
        message=note.message,
        attachments=attachments_json,
        is_internal=True,  # Internal notes only visible to staff
    )

    db.add(db_reply)
    db.commit()

    return {"message": "Internal note added successfully"}


# License management endpoints
# TODO: These will integrate with the existing licensing module

@router.get("/licenses")
async def search_licenses(
    search: str = Query(..., description="Search by email or license key"),
    token: str = Query(..., description="JWT access token"),
):
    """Search licenses by email or key.

    Args:
        search: Search query
        token: JWT access token

    Returns:
        List of matching licenses

    Raises:
        HTTPException: If access denied
    """
    verify_admin_role(token)

    # TODO: Implement search in licensing module
    return []


@router.put("/licenses/{license_id}/extend")
async def extend_license(
    license_id: str,
    extend_data: LicenseExtend,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Extend license expiration.

    Args:
        license_id: License ID
        extend_data: Extension data
        token: JWT access token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If license not found or access denied
    """
    admin_id = verify_admin_role(token)

    # TODO: Implement license extension in licensing module

    # Log action
    log_admin_action(
        db,
        admin_id,
        AdminActionType.LICENSE_EXTENDED,
        "license",
        license_id,
        {"days": extend_data.days, "reason": extend_data.reason},
    )

    return {"message": f"License extended by {extend_data.days} days"}


@router.delete("/licenses/{license_id}")
async def revoke_license(
    license_id: str,
    revoke_data: LicenseRevoke,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db),
):
    """Revoke a license.

    Args:
        license_id: License ID
        revoke_data: Revocation data
        token: JWT access token
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If license not found or access denied
    """
    admin_id = verify_admin_role(token)

    # TODO: Implement license revocation in licensing module

    # Log action
    log_admin_action(
        db,
        admin_id,
        AdminActionType.LICENSE_REVOKED,
        "license",
        license_id,
        {"reason": revoke_data.reason},
    )

    return {"message": "License revoked successfully"}
