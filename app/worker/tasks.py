import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.core.database import async_session_factory
from app.events.models import Event
from app.tickets.models import Ticket
from app.users.models import User
from app.services.email import send_reminder_email
from sqlalchemy import select, and_, update

logger = logging.getLogger("uvicorn")

async def send_event_reminders():
    logger.info("WORKER: Checking for upcoming events...")
    # We manually open a connection because we are outside the API request cycle
    async with async_session_factory() as db:
        # We look for events starting between 24 hours from now and 25 hours from now.
        now = datetime.now(timezone.utc)
        start_window = now + timedelta(days=1) 
        end_window = start_window + timedelta(hours=1)

        result = await db.execute(
            select(Event).where(
                and_(
                    Event.event_time >= start_window, 
                    Event.event_time < end_window
                )
            )
        )
        upcoming_events = result.scalars().all()
        if not upcoming_events:
            logger.info("No events found starting in the 24h window.")
            return 
    
        for event in upcoming_events:
            logger.info(f" Found Event: {event.name} (ID: {event.id})")     
            # Fetch tickets and load the User (owner)
            ticket_query = await db.execute(
                select(Ticket)
                .where(Ticket.event_id == event.id)
                .options(selectinload(Ticket.owner)) 
            )
            tickets = ticket_query.scalars().all()

            if not tickets:
                logger.info(f"   Event {event.name} has no tickets sold.")
                continue
            logger.info(f"Processing {len(tickets)} tickets...")
            
            for ticket in tickets:
                if ticket.owner and ticket.owner.email:
                    user_email = ticket.owner.email
                    
                    await send_reminder_email(
                    email_to=user_email,
                    event_name=event.name,
                    event_time=event.date,
                    ticket_code=ticket.confirmation_code)
                else:
                    logger.warning(f"   Ticket {ticket.id} has no valid owner/email.")
    logger.info("WORKER: Reminder check complete.")



# ---CLEANUP  ---
"""
    Runs once a day.
    Finds events where date < NOW and status is still 'UPCOMING'.
    Updates them to 'COMPLETED'.
"""
async def close_expired_events():
    logger.info("WORKER: Cleaning up expired events...")
    async with async_session_factory() as db:
        now = datetime.utcnow()
        
        # This translates to: UPDATE events SET status='COMPLETED' WHERE date < now AND status='UPCOMING'
        statement = (
            update(Event)
            .where(
                and_(
                    Event.date < now,
                    Event.status == "UPCOMING"
                )
            )
            .values(status="COMPLETED")
        )
        
        result = await db.execute(statement)
        await db.commit() 
        logger.info(f"Cleanup Complete. Closed {result.rowcount} events.")