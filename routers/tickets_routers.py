from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core import rbac 
from app.users.models import User
from app.users.enums import UserRole 
from app.tickets.models import Ticket
from app.events.models import Event
from app.tickets.schemas import TicketRead
from app.tickets.services import TicketService
from app.core.throttling import limiter

from app.core.pagination import PaginationParams, PaginatedResponse, paginate

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.get("/my-tickets", response_model=PaginatedResponse[TicketRead])
@limiter.limit("30/minute")
async def get_my_tickets(
    request: Request,
    params: PaginationParams = Depends(), 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        rbac.get_current_user_with_role(UserRole.USER)
    )):
    query = (
        select(Ticket)
        .join(Event, Ticket.event_id == Event.id)
        .where(Ticket.user_id == current_user.id)
        .where(Event.event_time > func.now()) 
        .order_by(Event.event_time.asc())
        .options(selectinload(Ticket.event))  
    )
    return await paginate(db, query, params, TicketRead)


@router.post("/{event_id}/buy")
@limiter.limit("5/minute")
async def buy_ticket(
    request: Request,
    event_id : int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        rbac.get_current_user_with_role(UserRole.USER)
    )
):
    return await TicketService.buy_ticket(
        db=db, event_id=event_id, user=current_user)

