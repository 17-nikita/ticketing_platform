# events_routers.py
from fastapi import APIRouter, Depends, status,Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core import rbac 
from app.users.models import User
from app.events.models import Event 
from sqlalchemy import select
from app.users.enums import UserRole 
from app.events.schemas import EventRead, EventCreate, EventUpdate
from app.events.services import EventService
from app.tickets.services import TicketService
from app.core.throttling import limiter
from app.events.ticketmaster_service import TicketmasterService
from app.core.pagination import PaginationParams, PaginatedResponse, paginate

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

# --- PUBLIC ENDPOINTS  ---

@router.get("/", response_model=PaginatedResponse[EventRead])
@limiter.limit("30/minute")
async def get_all_events(
    request: Request,
    params: PaginationParams = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    query = select(Event).order_by(Event.id)
    return await paginate(db, query, params, EventRead)


@router.get("/{event_id}", response_model=EventRead)
@limiter.limit("30/minute")
async def get_event_details(request: Request,event_id: int, db: AsyncSession = Depends(get_db)):
    return await EventService.get_event_by_id(db, event_id)

# --- 'EVENT_MANAGER' ROLE ENDPOINTS ---

@router.post(
    "/create", 
    response_model=EventRead, 
    status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_event(request: Request,
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db),
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER))):

    return await EventService.create_event(
        db=db, event_data=event_data, manager=current_manager)


@router.post("/import-ticketmaster", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def import_external_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(rbac.get_current_user)
):
    return await TicketmasterService.fetch_and_save_events(db, manager_id=current_user.id)

@router.patch("/update/{event_id}", response_model=EventRead)
@limiter.limit("10/minute")
async def update_event(
    request: Request,
    event_id: int,
    update_data: EventUpdate,
    db: AsyncSession = Depends(get_db),
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
@limiter.limit("10/minute")
async def delete_event(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_manager: User = Depends(
        rbac.get_current_user_with_role(UserRole.EVENT_MANAGER)
        )):
    return await EventService.delete_event(
        db=db, event_id=event_id, manager=current_manager)
    