import logging # <--- Added import
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.events.models import Event
from app.events.schemas import EventCreate, EventUpdate
from app.users.models import User
from app.core.exceptions import CustomError

# <--- Initialize Logger
logger = logging.getLogger(__name__)

class EventService:
    @staticmethod
    async def get_event_by_id(db: AsyncSession, event_id: int) -> Event:
        logger.debug(f"Fetching event details for ID: {event_id}")
        
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalars().first()
        
        if not event:
            logger.warning(f"Event lookup failed: Event ID {event_id} not found.") # <--- Log failure
            raise CustomError(message="Event not found", status_code=status.HTTP_404_NOT_FOUND)
        return event

    # @staticmethod
    # async def get_all_events(db: AsyncSession) -> list[Event]:
    #     logger.debug("Fetching list of all events.") # <--- Log entry
    #     result = await db.execute(select(Event).order_by(Event.id))
    #     return result.scalars().all()


    @staticmethod
    async def create_event(
        db: AsyncSession, event_data: EventCreate, manager: User) -> Event:
        
        logger.info(f"Manager {manager.email} (ID: {manager.id}) is creating event: '{event_data.name}'") # <--- Log entry
        
        new_event = Event(
            name=event_data.name,
            description=event_data.description,
            event_time=event_data.event_time,
            total_tickets=event_data.total_tickets,
            available_tickets=event_data.total_tickets, 
            ticket_price=event_data.ticket_price, 
            manager_id=manager.id 
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        
        logger.info(f"Event created successfully: '{new_event.name}' (ID: {new_event.id})") # <--- Log success
        return new_event

    @staticmethod
    async def update_event(
        db: AsyncSession, event_id: int, payload: EventUpdate, manager: User
    ) -> Event:
        logger.info(f"Manager {manager.id} attempting to update event {event_id}") # <--- Log entry
       
        event = await EventService.get_event_by_id(db, event_id)
        
        # check permission
        if event.manager_id != manager.id:
            logger.warning(f"Update failed: Manager {manager.id} unauthorized to edit event {event_id}") # <--- Log failure
            raise CustomError(message="You do not have permission to edit this event", status_code=status.HTTP_403_FORBIDDEN)

        # it convets pydantic object into python dictionary
        update_data = payload.model_dump(exclude_unset=True)

        
        if "total_tickets" in update_data:
            new_total = update_data["total_tickets"]
            old_total = event.total_tickets
            
            # Calculate sold tickets
            tickets_sold = old_total - event.available_tickets
            
            # Validation: You cannot reduce total tickets below the amount already sold
            if new_total < tickets_sold:
                error_msg = f"Cannot reduce total tickets to {new_total}. {tickets_sold} tickets have already been sold."
                logger.warning(f"Update validation failed for event {event_id}: {error_msg}") # <--- Log failure
                raise CustomError(message=error_msg, status_code=status.HTTP_400_BAD_REQUEST)

            diff = new_total - old_total
            event.available_tickets += diff

        for key, value in update_data.items():
            setattr(event, key, value)
        
        await db.commit()
        await db.refresh(event)
        
        logger.info(f"Event {event_id} updated successfully.") # <--- Log success
        return event
    

    @staticmethod
    async def delete_event(
        db: AsyncSession, event_id: int, manager: User):
        
        logger.info(f"Manager {manager.id} attempting to delete event {event_id}") # <--- Log entry
        
        event = await EventService.get_event_by_id(db, event_id)

        # check Permission
        if event.manager_id != manager.id:
            logger.warning(f"Delete failed: Manager {manager.id} unauthorized to delete event {event_id}") # <--- Log failure
            raise CustomError(message="You do not have permission to delete this event", status_code=status.HTTP_403_FORBIDDEN)

        await db.delete(event)
        await db.commit()
        
        logger.info(f"Event {event_id} deleted successfully.") # <--- Log success
        return {"message": "Event deleted successfully"}