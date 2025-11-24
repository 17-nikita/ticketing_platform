from fastapi import APIRouter, Depends,Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core import rbac 
from typing import List
from app.users.models import User
from app.users.enums import UserRole 
from app.tickets.schemas import TicketRead
from app.tickets.services import TicketService
from app.core.throttling import limiter

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.get("/my-tickets", response_model=List[TicketRead])
@limiter.limit("30/minute")
async def get_my_tickets(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        rbac.get_current_user_with_role(UserRole.USER)
    )):
    return await TicketService.get_user_tickets(db, current_user)


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

