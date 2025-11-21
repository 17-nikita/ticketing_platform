from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.tickets.models import Ticket
from app.events.models import Event
from app.users.models import User
from app.services.email import send_ticket_confirmation

class TicketService:

    @staticmethod
    async def get_user_tickets(db: AsyncSession, user: User) -> list[Ticket]:
        # 'selectinload' joins the Event table so we can see event names
        result = await db.execute(
            select(Ticket)
            .where(Ticket.user_id == user.id)
            .options(selectinload(Ticket.event)) 
        )
        return result.scalars().all()

    @staticmethod
    async def buy_ticket(db: AsyncSession, event_id: int, user: User) -> dict:
        async with db.begin():
            result = await db.execute(
                select(Event).where(Event.id == event_id).with_for_update()
            )
            event = result.scalars().first()

            if not event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

            # Check Availability
            if event.available_tickets < 1:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Sold Out")

            #Update Inventory
            event.available_tickets -= 1
            
            # Create Ticket
            new_ticket = Ticket(user_id=user.id, event_id=event.id)
            db.add(new_ticket)
            
    
            await db.flush()
            await db.refresh(new_ticket)

        await send_ticket_confirmation(user.email, new_ticket, event)

        return {
            "message": "Ticket purchased successfully",
            "ticket_code": new_ticket.confirmation_code,
            "event": event.name
        }