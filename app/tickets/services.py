from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.events.models import Event
from app.users.models import User
from app.tickets.models import Ticket
from app.services.email import send_ticket_confirmation 

class TicketService:

    # Gets all tickets owned by a specific user.
    @staticmethod
    async def get_user_tickets(db: AsyncSession, *, user: User) -> list[Ticket]:
        result = await db.execute(
            select(Ticket).where(Ticket.user_id == user.id)
        )
        return result.scalars().all()

    @staticmethod
    async def buy_ticket(db: AsyncSession, *, event_id: int, user: User) -> dict: 
        # 'db.begin()' starts a database transaction.
        # If any error happens inside, the database auto-rolls back.
        async with db.begin():
            # 1. Get the event and LOCK IT for this transaction.
            # 'with_for_update=True' prevents a race condition
            # where two users buy the last ticket at the same time.
            result = await db.execute(
                select(Event)
                .where(Event.id == event_id)
                .with_for_update()
            )
            event = result.scalars().first()

            if not event:
                raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")

            # 2. Check if tickets are available
            if event.available_tickets <= 0:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "No tickets available")

            # 3. All checks passed. Decrement ticket count.
            event.available_tickets -= 1
            
            # 4. Create the new ticket record
            new_ticket = Ticket(user_id=user.id, event_id=event.id)
            db.add(new_ticket)
            
            # 5. The transaction is committed here, saving both
            # the change to the 'event' and the new 'ticket'.

            await db.flush()
            await db.refresh(new_ticket)


        # 6. (Optional) Send confirmation email *after* success
        # await send_ticket_confirmation(user.email, new_ticket)
        await send_ticket_confirmation(user.email, new_ticket, event)
        
        return {
            "message": "Ticket purchased successfully!", 
            "ticket_code": new_ticket.confirmation_code
        }