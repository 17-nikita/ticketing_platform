import logging 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.services.payment import create_checkout_session
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
        """
        PHASE 1: INITIATE
        Checks availability and generates the Stripe Payment Link.
        Does NOT create the ticket yet.
        """
        logger.info(f"User {user.id} initiating purchase for Event {event_id}")

        event = await db.get(Event, event_id)
        
        if not event:
            logger.warning(f"Purchase init failed: Event {event_id} not found")
            raise CustomError(message="Event not found", status_code=status.HTTP_404_NOT_FOUND)

        if event.available_tickets < 1:
            logger.warning(f"Purchase init failed: Event {event_id} is Sold Out")
            raise CustomError(message="Sold Out", status_code=status.HTTP_400_BAD_REQUEST)

        # Generate Stripe Checkout Session
        payment_url = create_checkout_session(
            event_id=event.id,
            event_name=event.name,
            user_id=user.id,
            user_email=user.email,
            amount=event.ticket_price 
        )

        if not payment_url:
            logger.error(f"Failed to generate payment URL for User {user.id}, Event {event_id}")
            raise CustomError(message="Payment gateway error", status_code=status.HTTP_502_BAD_GATEWAY)

        logger.info(f"Payment URL generated for User {user.id}, Event {event_id}")

        return {
            "message": "Payment initiated. Please complete payment.",
            "payment_url": payment_url
        }

    @staticmethod
    async def finalize_ticket_creation(db: AsyncSession, event_id: int, user_id: int, stripe_session_id: str) -> Ticket:
        """
        PHASE 2: FINALIZE (Called by Webhook)
        Creates the ticket, decrements inventory safely, and handles idempotency.
        """
        logger.info(f"Finalizing ticket for Stripe Session: {stripe_session_id}")

        # --- 1. Idempotency Check ---
        # Before doing anything, check if we already processed this webhook.
        query = select(Ticket).where(Ticket.stripe_session_id == stripe_session_id)
        result = await db.execute(query)
        existing_ticket = result.scalars().first()

        if existing_ticket:
            logger.info(f"Duplicate Webhook ignored for Session {stripe_session_id}")
            return existing_ticket 

        # --- 2. Fetch User ---
        user = await db.get(User, user_id)
        if not user:
            logger.error(f"Webhook failed: User {user_id} not found")
            raise CustomError(message="User not found", status_code=status.HTTP_404_NOT_FOUND)

        # --- 3. Transaction with Locking ---
        async with db.begin():
            # Lock the event row immediately
            # This forces other transactions to WAIT until we are done
            query = select(Event).where(Event.id == event_id).with_for_update()
            result = await db.execute(query)
            event = result.scalar_one_or_none()
            
            if not event:
                logger.error(f"Webhook failed: Event {event_id} not found")
                raise CustomError(message="Event not found", status_code=status.HTTP_404_NOT_FOUND)
            
            # Check inventory safely inside the lock
            if event.available_tickets < 1:
                logger.error(f"Webhook failed: Event {event_id} is Sold Out (Race condition caught!)")
                # TODO: Call Stripe API here to refund the user's money 
                # stripe.Refund.create(payment_intent=...)
                raise CustomError(message="Sold Out", status_code=status.HTTP_400_BAD_REQUEST)

            # Decrement Inventory
            event.available_tickets -= 1
            
            # Create Ticket with the session ID
            new_ticket = Ticket(
                user_id=user.id, 
                event_id=event.id,
                stripe_session_id=stripe_session_id
            )
            db.add(new_ticket)
            
            # Transaction commits automatically here, releasing the lock

        # --- 4. Refresh & Email ---
        await db.refresh(new_ticket)
        # Load the event relationship so we can use event details in the email
        await db.refresh(new_ticket, attribute_names=["event"])

        logger.info(f"Ticket purchased successfully. ID: {new_ticket.id}")

        try:
            await send_ticket_confirmation(user.email, new_ticket)
            logger.info(f"Confirmation email sent to {user.email}")
        except Exception as e:
            sentry_sdk.capture_exception(e)
            logger.error(f"Failed to send email. Error: {e}", exc_info=True)

        return new_ticket