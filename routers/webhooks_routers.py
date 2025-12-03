# webhook routers.py file
from fastapi import APIRouter, Request, Header, HTTPException
import stripe
from app.core.config import settings
from app.core.database import async_session_factory
from app.tickets.services import TicketService 
import json # Import this to print the payload nicely

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/stripe")
async def stripe_webhook(
    request: Request, 
    stripe_signature: str = Header(None)
):
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        print("❌ Error: Invalid Payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        print("❌ Error: Invalid Signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # DEBUG PRINT: Tell us what event arrived
    print(f"📩 Event Received: {event['type']}")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # DEBUG PRINT: Show me the metadata!
        print(f"🔍 Session Metadata: {session.get('metadata')}")

        metadata = session.get("metadata", {})
        
        try:
            user_id = int(metadata.get("user_id"))
            event_id = int(metadata.get("event_id"))
        except (TypeError, ValueError):
            print("❌ Error: Metadata is missing user_id or event_id!")
            return {"status": "ignored", "reason": "missing metadata"}
        
        stripe_session_id = session.get("id")
        print(f"💰 Processing Payment for User {user_id}, Event {event_id}")

        async with async_session_factory() as db:
            try:
                await TicketService.finalize_ticket_creation(
                    db=db, 
                    event_id=event_id, 
                    user_id=user_id,
                    stripe_session_id=stripe_session_id
                )
            except Exception as e:
                print(f"❌ Error finalizing ticket: {e}")
                return {"status": "error", "detail": str(e)}

    return {"status": "success"}