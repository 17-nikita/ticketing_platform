from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core import rbac 
from app.users.models import User
from app.users.enums import UserRole 
from app.events.schemas import EventRead, EventCreate, EventUpdate
from app.events.services import EventService
from app.tickets.services import TicketService

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

# --- PUBLIC ENDPOINTS  ---

@router.get("/", response_model=list[EventRead])
async def get_all_events(db: AsyncSession = Depends(get_db)):
    return await EventService.get_all_events(db)

@router.get("/{event_id}", response_model=EventRead)
async def get_event_details(event_id: int, db: AsyncSession = Depends(get_db)):
    return await EventService.get_event_by_id(db, event_id)

# --- 'EVENT_MANAGER' ROLE ENDPOINTS ---

@router.post(
    "/create", 
    response_model=EventRead, 
    status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER))):

    return await EventService.create_event(
        db=db, event_data=event_data, manager=current_manager)

@router.put("/update/{event_id}", response_model=EventRead)
async def update_event(
    event_id: int,
    update_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    # GUARD: Only 'EVENT_MANAGER' roles can call this.
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
    )
):
    return await EventService.update_event(
        db=db, 
        event_id=event_id, 
        payload=update_data, 
        manager=current_manager
    )

@router.delete("/delete/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
        )):
    return await EventService.delete_event(
        db=db, event_id=event_id, manager=current_manager)
    