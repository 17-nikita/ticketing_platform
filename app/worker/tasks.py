import logging
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_ ,func,update
from sqlalchemy.orm import selectinload
from app.core.database import async_session_factory
from app.events.models import Event
from app.tickets.models import Ticket
from app.users.models import User
from app.services.email import send_reminder_email
from sqlalchemy import select, and_, update

logger = logging.getLogger(__name__)

async def send_event_reminders():
    logger.info("WORKER: Checking for upcoming events...")
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)
        
        # --- OPTION 1: Real Production Logic (24 hours before) ---
        start_window = now + timedelta(days=1) 
        end_window = start_window + timedelta(hours=1)

        # --- OPTION 2: Testing Logic (Check for events in the next 1 hour) ---
        # Use this to test with your event today!
        # start_window = now
        # end_window = now + timedelta(hours=24) # Broad window just to find your event for testing

        logger.info(f"Scanning for events between {start_window} and {end_window}")

        #  Use selectinload to fetch Tickets AND Owners in one go
        # This prevents the "N+1 query" problem and simplifies the loop
        query = (
            select(Event)
            .where(
                and_(
                    Event.event_time >= start_window, 
                    Event.event_time < end_window
                )
            )
            .options(selectinload(Event.tickets).selectinload(Ticket.owner))
        )
        
        result = await db.execute(query)
        upcoming_events = result.scalars().all()

        if not upcoming_events:
            logger.info("No events found in this window.")
            return 
        for event in upcoming_events:
            logger.info(f" Found Event: {event.name} (ID: {event.id})")     
            tickets = event.tickets 
            if not tickets:
                logger.info(f"   Event {event.name} has no tickets sold.")
                continue
                
            logger.info(f"Processing {len(tickets)} tickets...")
            
            for ticket in tickets:
                if ticket.owner and ticket.owner.email:
                    logger.info(f"   Sending email to: {ticket.owner.email}") 
                    # 1. Convert UTC (Database) -> IST (India Time)
                    # The DB gives you raw UTC. We shift it +5:30 here.
                    ist_time = event.event_time.astimezone(ZoneInfo("Asia/Kolkata"))
                    
                    # 2. Format it to match your Schema style ("25-11-2025 03:39 PM")
                    formatted_time_str = ist_time.strftime("%d-%m-%Y %I:%M %p")   
                    await send_reminder_email(
                        email_to=ticket.owner.email,
                        event_name=event.name,
                        event_time=formatted_time_str,
                        ticket_code=ticket.confirmation_code
                    )
                else:
                    logger.warning(f"   Ticket {ticket.id} has no valid owner/email.")
                    
    logger.info("WORKER: Reminder check complete.")


async def close_expired_events():
    logger.info("WORKER: Cleaning up expired events...")
    async with async_session_factory() as db:
        now = datetime.utcnow()
        
        # This translates to: UPDATE events SET status='COMPLETED' WHERE date < now AND status='UPCOMING'
        statement = (
            update(Event)
            .where(
                and_(
                    Event.event_time < func.now(),
                    Event.status == "UPCOMING"
                )
            )
            .values(status="COMPLETED")
        )
        
        result = await db.execute(statement)
        await db.commit() 
        logger.info(f"Cleanup Complete. Closed {result.rowcount} events.")