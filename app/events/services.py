from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.events.models import Event
from app.events.schemas import EventCreate, EventUpdate
from app.users.models import User

class EventService:
    """
    Service class for all event-related logic.
    Combines business logic and database operations (CRUD).
    """

    # --- CRUD (Read) ---
    
    @staticmethod
    async def get_event_by_id(db: AsyncSession, event_id: int) -> Event | None:
        result = await db.execute(select(Event).where(Event.id == event_id))
        return result.scalars().first()

    @staticmethod
    async def get_all_events(db: AsyncSession) -> list[Event]:
        result = await db.execute(select(Event).order_by(Event.event_time))
        return result.scalars().all()

    # --- Helper Methods ---
    
    @staticmethod
    async def get_event_or_404(db: AsyncSession, event_id: int) -> Event:
        """Helper to get an event or raise a 404."""
        event = await EventService.get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
        return event

    @staticmethod
    def check_manager_permission(event: Event, manager: User):
        """
        Checks if the manager is the owner of the event.
        This is a business logic rule.
        """
        if event.manager_id != manager.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "You do not have permission to modify this event."
            )

    # --- CRUD (Create, Update, Delete) ---

    @staticmethod
    async def create_event(
        db: AsyncSession, *, event_data: EventCreate, manager: User
    ) -> Event:
        """
        Creates a new event.
        """
        new_event = Event(
            name=event_data.name,
            description=event_data.description,
            event_time=event_data.event_time,
            total_tickets=event_data.total_tickets,
            # At creation, available tickets = total tickets
            available_tickets=event_data.total_tickets, 
            manager_id=manager.id # Set the owner
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        return new_event

    @staticmethod
    async def update_event(
        db: AsyncSession, *, event_id: int, update_data: EventUpdate, manager: User
    ) -> Event:
        """
        Updates an event, but only if the manager is the owner.
        """
        event = await EventService.get_event_or_404(db, event_id)
        
        # Authorization Check
        EventService.check_manager_permission(event, manager)

        update_dict = update_data.model_dump(exclude_unset=True) 
        
        for key, value in update_dict.items():
            setattr(event, key, value)
            
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def delete_event(
        db: AsyncSession, *, event_id: int, manager: User
    ):
        """
        Deletes an event, but only if the manager is the owner.
        """
        event = await EventService.get_event_or_404(db, event_id)
        
        # Authorization Check
        EventService.check_manager_permission(event, manager)
        
        await db.delete(event)
        await db.commit()
        return {"message": "Event deleted successfully"}