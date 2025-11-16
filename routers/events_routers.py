from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core import rbac # <-- Your RBAC guards
from app.users.models import User
from app.users.enums import UserRole # <-- Your roles
from app.events.schemas import EventRead, EventCreate, EventUpdate
from app.events.services import EventService
from app.tickets.services import TicketService

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

# --- PUBLIC ENDPOINTS (for everyone) ---

@router.get("/", response_model=list[EventRead])
async def get_all_events(db: AsyncSession = Depends(get_db)):
    """
    Returns a list of all upcoming events. (Public)
    """
    return await EventService.get_all_events(db)

@router.get("/{event_id}", response_model=EventRead)
async def get_event(event_id: int, db: AsyncSession = Depends(get_db)):
    """
    Returns details for a single event. (Public)
    """
    return await EventService.get_event_or_404(db, event_id)

# --- 'USER' ROLE ENDPOINTS ---

@router.post("/{event_id}/buy")
async def buy_ticket(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'USER' roles can call this.
    current_user: User = Depends(
        rbac.get_current_user_with_role(UserRole.USER)
    )
):
    """
    Buys a ticket for an event. (Users Only)
    """
    # This calls the service from the Ticket module
    return await TicketService.buy_ticket(
        db=db, event_id=event_id, user=current_user
    )

# --- 'EVENT_MANAGER' ROLE ENDPOINTS ---

@router.post(
    "/", 
    response_model=EventRead, 
    status_code=status.HTTP_201_CREATED
)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'EVENT_MANAGER' roles can call this.
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
    )
):
    """
    Creates a new event. (Event Managers Only)
    """
    return await EventService.create_event(
        db=db, event_data=event_data, manager=current_manager
    )

@router.put("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    update_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'EVENT_MANAGER' roles can call this.
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
    )
):
    """
    Updates an event. (Event Managers Only & Owner)
    """
    return await EventService.update_event(
        db=db, 
        event_id=event_id, 
        update_data=update_data, 
        manager=current_manager
    )

@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'EVENT_MANAGER' roles can call this.
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
    )
):
    """
    Deletes an event. (Event Managers Only & Owner)
    """
    await EventService.delete_event(
        db=db, event_id=event_id, manager=current_manager
    )
    # 204 No Content response should not have a body
    return None