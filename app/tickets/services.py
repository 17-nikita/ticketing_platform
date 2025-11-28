import logging # <--- Added import
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.tickets.models import Ticket
from app.events.models import Event
from app.users.models import User
from app.services.email import send_ticket_confirmation
import sentry_sdk
from app.core.exceptions import CustomError

# <--- Initialize Logger
logger = logging.getLogger(__name__)

'''selectinload tells the database: "While you are grabbing the tickets, 
    please also grab the Event details associated with them right now.'''
class TicketService:

    @staticmethod
    async def get_user_tickets(db: AsyncSession, user: User) -> list[Ticket]:
        logger.debug(f"Fetching ALL tickets for user {user.email} (ID: {user.id})")

        result = await db.execute(
            select(Ticket)
            .join(Event, Ticket.event_id == Event.id)
            .where(Ticket.user_id == user.id)
            .where(Event.event_time > func.now())      
            .order_by(Event.event_time.asc())          
            .options(selectinload(Ticket.event))       
        )
        tickets = result.scalars().all()
        logger.debug(f"Found {len(tickets)} tickets for user {user.id}")
        return tickets
    


    @staticmethod
    async def buy_ticket(db: AsyncSession, event_id: int, user: User) -> dict:
        logger.info(f"User {user.id} attempting to buy ticket for Event {event_id}") # <--- Log entry

        event = await db.get(Event, event_id)
       
        if not event:
            logger.warning(f"Ticket purchase failed: Event {event_id} not found") # <--- Log failure
            raise CustomError(message="Event not found", status_code=status.HTTP_404_NOT_FOUND)
 
        if event.available_tickets < 1:
            logger.warning(f"Ticket purchase failed: Event {event_id} is Sold Out") # <--- Log failure
            raise CustomError(message="Sold Out", status_code=status.HTTP_400_BAD_REQUEST)
       
        event.available_tickets -= 1
            
        # Create Ticket
        new_ticket = Ticket(user_id=user.id, event_id=event.id)
        db.add(new_ticket)
        await db.commit()
        await db.refresh(new_ticket)
        
        logger.info(f"Ticket purchased successfully. ID: {new_ticket.id}, Code: {new_ticket.confirmation_code}") # <--- Log success

        try:
            await send_ticket_confirmation(user.email, new_ticket, event)
            logger.info(f"Confirmation email sent to {user.email}") # <--- Log email success
        except Exception as e:
            # We capture in Sentry AND log it to our file
            sentry_sdk.capture_exception(e)
            logger.error(f"Failed to send ticket confirmation email to {user.email}. Error: {e}", exc_info=True) # <--- Log error with traceback

        return {
            "message": "Ticket purchased successfully",
            "ticket_code": new_ticket.confirmation_code,
            "event": event.name
        }