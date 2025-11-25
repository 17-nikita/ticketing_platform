from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.tickets.models import Ticket
from app.events.models import Event
from app.users.models import User
from app.services.email import send_ticket_confirmation

'''selectinload tells the database: "While you are grabbing the tickets, 
    please also grab the Event details associated with them right now.'''
class TicketService:

    @staticmethod
    async def get_user_tickets(db: AsyncSession, user: User) -> list[Ticket]:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.user_id == user.id)
            .options(selectinload(Ticket.event)) 
        )
        return result.scalars().all()

    @staticmethod
    async def buy_ticket(db: AsyncSession, event_id: int, user: User) -> dict:
        event = await db.get(Event, event_id)
       
        if not event:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

    
        if event.available_tickets < 1:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sold Out")

           
        event.available_tickets -= 1
            
        # Create Ticket
        new_ticket = Ticket(user_id=user.id, event_id=event.id)
        db.add(new_ticket)
        await db.commit()
        await db.refresh(new_ticket)
        try:
            await send_ticket_confirmation(user.email, new_ticket, event)
        except Exception as e:
            print(f"Warning: Ticket sold but email failed to send. Error: {e}")

        return {
            "message": "Ticket purchased successfully",
            "ticket_code": new_ticket.confirmation_code,
            "event": event.name
        }