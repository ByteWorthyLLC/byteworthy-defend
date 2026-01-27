"""Database module for HifzDefend customer portal."""

from .engine import get_db, init_db
from .models import (
    AdminLog,
    DiscountCode,
    Ticket,
    TicketReply,
)

__all__ = [
    "get_db",
    "init_db",
    "Ticket",
    "TicketReply",
    "AdminLog",
    "DiscountCode",
]
