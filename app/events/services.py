from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.events.models import Event
from app.events.schemas import EventCreate, EventUpdate
from app.users.models import User
from app.core.exceptions import CustomError

class EventService:
    @staticmethod
    async def get_event_by_id(db: AsyncSession, event_id: int) -> Event:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalars().first()
        if not event:
            raise CustomError(message="Event not found",status_code=status.HTTP_404_NOT_FOUND)
        return event

    @staticmethod
    async def get_all_events(db: AsyncSession) -> list[Event]:
        result = await db.execute(select(Event).order_by(Event.event_time))
        return result.scalars().all()


    @staticmethod
    async def create_event(
        db: AsyncSession, event_data: EventCreate, manager: User) -> Event:
        new_event = Event(
            name=event_data.name,
            description=event_data.description,
            event_time=event_data.event_time,
            total_tickets=event_data.total_tickets,
            available_tickets=event_data.total_tickets, 
            manager_id=manager.id 
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        return new_event

    @staticmethod
    async def update_event(
        db: AsyncSession, event_id: int, payload: EventUpdate, manager: User
    ) -> Event:
       
        event = await EventService.get_event_by_id(db, event_id)
        # check permission
        if event.manager_id != manager.id:
            raise CustomError(message="You do not have permission to edit this event",status_code=status.HTTP_403_FORBIDDEN)

        # it convets pydantic object into python dictionary
        update_data = payload.model_dump(exclude_unset=True)

        
        if "total_tickets" in update_data:
            new_total = update_data["total_tickets"]
            old_total = event.total_tickets
            
            # Calculate sold tickets
            tickets_sold = old_total - event.available_tickets
            
            # Validation: You cannot reduce total tickets below the amount already sold
            if new_total < tickets_sold:
                raise CustomError(message=f"Cannot reduce total tickets to {new_total}. {tickets_sold} tickets have already been sold.",status_code=status.HTTP_400_BAD_REQUEST)

            diff = new_total - old_total
            event.available_tickets += diff

        for key, value in update_data.items():
            setattr(event, key, value)
        await db.commit()
        await db.refresh(event)
        return event
    

    @staticmethod
    async def delete_event(
        db: AsyncSession, event_id: int, manager: User):
        event = await EventService.get_event_by_id(db, event_id)

        # check Permission
        if event.manager_id != manager.id:
            raise CustomError(message="You do not have permission to delete this event",status_code=status.HTTP_403_FORBIDDEN)

        await db.delete(event)
        await db.commit()
        return {"message": "Event deleted successfully"}