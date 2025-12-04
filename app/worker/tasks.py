# import logging
# from zoneinfo import ZoneInfo
# from datetime import datetime, timedelta, timezone
# from sqlalchemy import select, and_ ,func,update
# from sqlalchemy.orm import selectinload
# from app.core.database import async_session_factory
# from app.events.models import Event
# from app.tickets.models import Ticket
# from app.users.models import User
# from app.services.email import send_reminder_email,send_cart_initial_email, send_cart_followup_email
# from sqlalchemy import select, and_, update
# from celery import shared_task
# from app.core.celery_app import celery_app
# from app.core.config import settings
# import redis 
# import json
# import asyncio


# redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
# logger = logging.getLogger(__name__)

# async def send_event_reminders():
#     logger.info("WORKER: Checking for upcoming events...")
#     async with async_session_factory() as db:
#         now = datetime.now(timezone.utc)
        
#         # --- OPTION 1: Real Production Logic (24 hours before) ---
#         start_window = now + timedelta(days=1) 
#         end_window = start_window + timedelta(hours=1)

#         # --- OPTION 2: Testing Logic (Check for events in the next 1 hour) ---
#         # Use this to test with your event today!
#         # start_window = now
#         # end_window = now + timedelta(hours=24) # Broad window just to find your event for testing

#         logger.info(f"Scanning for events between {start_window} and {end_window}")

#         #  Use selectinload to fetch Tickets AND Owners in one go
#         # This prevents the "N+1 query" problem and simplifies the loop
#         query = (
#             select(Event)
#             .where(
#                 and_(
#                     Event.event_time >= start_window, 
#                     Event.event_time < end_window
#                 )
#             )
#             .options(selectinload(Event.tickets).selectinload(Ticket.owner))
#         )
        
#         result = await db.execute(query)
#         upcoming_events = result.scalars().all()

#         if not upcoming_events:
#             logger.info("No events found in this window.")
#             return 
#         for event in upcoming_events:
#             logger.info(f" Found Event: {event.name} (ID: {event.id})")     
#             tickets = event.tickets 
#             if not tickets:
#                 logger.info(f"   Event {event.name} has no tickets sold.")
#                 continue
                
#             logger.info(f"Processing {len(tickets)} tickets...")
            
#             for ticket in tickets:
#                 if ticket.owner and ticket.owner.email:
#                     logger.info(f"   Sending email to: {ticket.owner.email}") 
#                     # 1. Convert UTC (Database) -> IST (India Time)
#                     # The DB gives you raw UTC. We shift it +5:30 here.
#                     ist_time = event.event_time.astimezone(ZoneInfo("Asia/Kolkata"))
                    
#                     # 2. Format it to match your Schema style ("25-11-2025 03:39 PM")
#                     formatted_time_str = ist_time.strftime("%d-%m-%Y %I:%M %p")   
#                     await send_reminder_email(
#                         email_to=ticket.owner.email,
#                         event_name=event.name,
#                         event_time=formatted_time_str,
#                         ticket_code=ticket.confirmation_code
#                     )
#                 else:
#                     logger.warning(f"   Ticket {ticket.id} has no valid owner/email.")
                    
#     logger.info("WORKER: Reminder check complete.")


# async def close_expired_events():
#     logger.info("WORKER: Cleaning up expired events...")
#     async with async_session_factory() as db:
#         now = datetime.utcnow()
        
#         # This translates to: UPDATE events SET status='COMPLETED' WHERE date < now AND status='UPCOMING'
#         statement = (
#             update(Event)
#             .where(
#                 and_(
#                     Event.event_time < func.now(),
#                     Event.status == "UPCOMING"
#                 )
#             )
#             .values(status="COMPLETED")
#         )
        
#         result = await db.execute(statement)
#         await db.commit() 
#         logger.info(f"Cleanup Complete. Closed {result.rowcount} events.")



# def revoke_task(task_id: str):
#     """Kills a scheduled task so it doesn't run."""
#     if task_id:
#         celery_app.control.revoke(task_id, terminate=True)

# def update_cart_task_id(user_id: int, event_id: int, new_task_id: str):
#     """
#     Updates the Redis Cart to track the NEW task ID.
#     If we don't do this, 'remove_from_cart' won't know which task to kill.
#     """
#     cart_key = f"cart:{user_id}"
#     raw_item = redis_client.hget(cart_key, str(event_id))
    
#     if raw_item:
#         item = json.loads(raw_item)
#         item["active_task_id"] = new_task_id
#         redis_client.hset(cart_key, str(event_id), json.dumps(item))

# # --- THE INITIAL TRIGGER ---
# @celery_app.task(name="send_initial_reminder")
# def send_initial_reminder(user_id: int, event_id: int, email: str, event_name: str,event_time_str: str):
#     print(f"📧 [INITIAL REMINDER] Sending reminder to {email} for '{event_name}'")
    
#     # 1. Run the Async Email Function
#     try:
#         asyncio.run(send_cart_initial_email(email, event_name))
#         print("✅ Email sent successfully.")
#     except Exception as e:
#         print(f"❌ Failed to send email: {e}")

#     # 2. Schedule the Next Step (Using your new MINS config)
#     next_eta = datetime.utcnow() + timedelta(minutes=settings.CART_FOLLOWUP_DELAY_MINS)
    
#     new_task = send_recurring_reminder.apply_async(
#         args=[user_id, event_id, email, event_name],
#         eta=next_eta
#     )
    
#     # Update Redis so we can kill this new task if they buy it
#     update_cart_task_id(user_id, event_id, new_task.id)


# # --- TASK 2: THE RECURSIVE LOOP ---
# @celery_app.task(name="send_recurring_reminder")
# def send_recurring_reminder(user_id: int, event_id: int, email: str, event_name: str):
#     print(f"📧 [RECURRING REMINDER] Sending follow-up to {email} for '{event_name}'")

#     # 1. Run the Async Email Function
#     try:
#         asyncio.run(send_cart_followup_email(email, event_name))
#         print("✅ Email sent successfully.")
#     except Exception as e:
#         print(f"❌ Failed to send email: {e}")
    
#     # 2. Schedule SELF again (Using your new MINS config)
#     next_eta = datetime.utcnow() + timedelta(minutes=settings.CART_RECURRING_DELAY_MINS)
    
#     new_task = send_recurring_reminder.apply_async(
#         args=[user_id, event_id, email, event_name],
#         eta=next_eta
#     )
    
#     # Update Redis again
#     update_cart_task_id(user_id, event_id, new_task.id)

import logging
import json
import asyncio
import redis
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from asgiref.sync import async_to_sync # <--- REQUIRED IMPORT

from sqlalchemy import select, update, and_, func
from sqlalchemy.orm import selectinload

# Project Imports
from app.core.database import async_session_factory
from app.core.config import settings
from app.core.redis_client import redis_pool
from app.core.celery_app import celery_app 

from app.events.models import Event
from app.tickets.models import Ticket
from app.services.email import (
    send_reminder_email, 
    send_cart_initial_email, 
    send_cart_followup_email
)

logger = logging.getLogger(__name__)

# --- HELPER FUNCTIONS ---

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool, decode_responses=True)

def revoke_task(task_id: str):
    if task_id:
        celery_app.control.revoke(task_id, terminate=True)

def update_cart_task_id(user_id: int, event_id: int, new_task_id: str):
    cart_key = f"cart:{user_id}"
    r = get_redis_client()
    try:
        raw_item = r.hget(cart_key, str(event_id))
        if raw_item:
            item = json.loads(raw_item)
            item["active_task_id"] = new_task_id
            r.hset(cart_key, str(event_id), json.dumps(item))
            logger.info(f"🔄 Updated Redis task_id for User {user_id}, Event {event_id} to {new_task_id}")
    except Exception as e:
        logger.error(f"Failed to update task ID in Redis: {e}")
    finally:
        r.close()

# --- DATABASE MAINTENANCE TASKS (WRAPPED FOR CELERY) ---

async def _send_event_reminders_logic():
    """
    INTERNAL ASYNC LOGIC: Checks for events starting soon and sends emails.
    """
    logger.info("WORKER: Checking for upcoming events...")
    async with async_session_factory() as db:
        now = datetime.now(timezone.utc)
        
        # Check window: Events starting between 24h and 25h from now
        start_window = now + timedelta(days=1) 
        end_window = start_window + timedelta(hours=1)

        logger.info(f"Scanning for events between {start_window} and {end_window}")

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
                continue
            
            for ticket in tickets:
                if ticket.owner and ticket.owner.email:
                    ist_time = event.event_time.astimezone(ZoneInfo("Asia/Kolkata"))
                    formatted_time_str = ist_time.strftime("%d-%m-%Y %I:%M %p")   
                    
                    await send_reminder_email(
                        email_to=ticket.owner.email,
                        event_name=event.name,
                        event_time=formatted_time_str,
                        ticket_code=ticket.confirmation_code
                    )
    logger.info("WORKER: Reminder check complete.")

@celery_app.task(name="send_event_reminders")
def send_event_reminders():
    """
    Celery Beat should call THIS task.
    It wraps the async logic using async_to_sync.
    """
    async_to_sync(_send_event_reminders_logic)()


# We can do the same for cleanup if you want to schedule it via Celery Beat
async def _close_expired_events_logic():
    logger.info("WORKER: Cleaning up expired events...")
    async with async_session_factory() as db:
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

@celery_app.task(name="close_expired_events")
def close_expired_events():
    async_to_sync(_close_expired_events_logic)()


# --- CELERY TASKS (CART ABANDONMENT) ---

@celery_app.task(name="send_initial_reminder")
def send_initial_reminder(user_id: int, event_id: int, email: str, event_name: str, event_time_str: str):
    # 1. Parse and Check Date
    try:
        event_time = datetime.fromisoformat(event_time_str)
        if event_time.tzinfo is not None:
            now = datetime.now(event_time.tzinfo)
        else:
            now = datetime.utcnow()

        if event_time < now:
            logger.info(f"🚫 Initial reminder skipped for {email}. Event '{event_name}' has already passed.")
            return "Event Passed"
    except Exception as e:
        logger.error(f"Date parsing error in reminder: {e}")

    logger.info(f"📧 [INITIAL REMINDER] Sending reminder to {email} for '{event_name}'")
    
    try:
        asyncio.run(send_cart_initial_email(email, event_name))
        logger.info("✅ Initial email sent successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to send initial email: {e}")

    # 3. Schedule the Next Step (Recursion)
    delay_mins = getattr(settings, 'CART_FOLLOWUP_DELAY_MINS', 30)
    next_eta = datetime.utcnow() + timedelta(minutes=delay_mins)
    
    new_task = send_recurring_reminder.apply_async(
        args=[user_id, event_id, email, event_name, event_time_str],
        eta=next_eta
    )
    update_cart_task_id(user_id, event_id, new_task.id)


@celery_app.task(name="send_recurring_reminder")
def send_recurring_reminder(user_id: int, event_id: int, email: str, event_name: str, event_time_str: str):
    # 1. Check Date (Stop recursion if event passed)
    try:
        event_time = datetime.fromisoformat(event_time_str)
        if event_time.tzinfo is not None:
            now = datetime.now(event_time.tzinfo)
        else:
            now = datetime.utcnow()

        if event_time < now:
            logger.info(f"🚫 Recurring loop stopping. Event '{event_name}' has passed.")
            return "Event Passed"
    except Exception:
        pass

    logger.info(f"📧 [RECURRING REMINDER] Sending follow-up to {email} for '{event_name}'")

    try:
        asyncio.run(send_cart_followup_email(email, event_name))
        logger.info("✅ Follow-up email sent successfully.")
    except Exception as e:
        logger.error(f"❌ Failed to send follow-up email: {e}")
    
    # 3. Schedule SELF again
    delay_mins = getattr(settings, 'CART_RECURRING_DELAY_MINS', 1440) 
    next_eta = datetime.utcnow() + timedelta(minutes=delay_mins)
    
    new_task = send_recurring_reminder.apply_async(
        args=[user_id, event_id, email, event_name, event_time_str],
        eta=next_eta
    )
    update_cart_task_id(user_id, event_id, new_task.id)