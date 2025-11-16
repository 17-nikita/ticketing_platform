from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core import rbac # <-- Your RBAC guards
from app.users.models import User
from app.users.enums import UserRole # <-- Your roles
from app.tickets.schemas import TicketRead
from app.tickets.services import TicketService

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.get("/my-tickets", response_model=list[TicketRead])
async def get_my_tickets(
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'USER' roles can call this.
    current_user: User = Depends(
        rbac.get_current_user_with_role(UserRole.USER)
    )
):
    """
    Returns a list of all tickets owned by the logged-in user.
    """
    return await TicketService.get_user_tickets(db=db, user=current_user)