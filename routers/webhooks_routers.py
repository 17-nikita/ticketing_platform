# from fastapi import APIRouter, Request, Header, HTTPException
# import stripe
# from app.core.config import settings
# from app.core.database import async_session_factory
# from app.tickets.services import TicketService 

# router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

# @router.post("/stripe")
# async def stripe_webhook(
#     request: Request, 
#     stripe_signature: str = Header(None)
# ):
#     """
#     1. Receives the raw request from Stripe.
#     2. Verifies the security signature.
#     3. Calls TicketService to finalize the ticket.
#     """
#     payload = await request.body()
    
#     try:
#         # 1. Verify Signature
#         event = stripe.Webhook.construct_event(
#             payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
#         )
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid payload")
#     except stripe.error.SignatureVerificationError:
#         raise HTTPException(status_code=400, detail="Invalid signature")

#     # 2. Handle Payment Success
#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']
        
#         # Get the IDs we hid in the metadata
#         metadata = session.get("metadata", {})
        
#         try:
#             user_id = int(metadata.get("user_id"))
#             event_id = int(metadata.get("event_id"))
#         except (TypeError, ValueError):
#             return {"status": "ignored", "reason": "missing metadata"}
        
#         # Extract the Stripe Session ID for idempotency check
#         stripe_session_id = session.get("id")

#         print(f"💰 Webhook received! User {user_id} paid for Event {event_id}")

#         # 3. Create Ticket (Finalize)
#         # We manually create a DB session here because Webhooks don't allow 
#         # standard 'Depends(get_db)' injection easily.
#         async with async_session_factory() as db:
#             try:
#                 await TicketService.finalize_ticket_creation(
#                     db=db, 
#                     event_id=event_id, 
#                     user_id=user_id,
#                     stripe_session_id=stripe_session_id
#                 )
#             except Exception as e:
#                 print(f"Error finalizing ticket: {e}")
#                 # We return 200 OK to Stripe even on logic error so they don't retry endlessly
#                 # In a real app, you would log this to Sentry/Alerting
#                 return {"status": "error", "detail": str(e)}

#     return {"status": "success"}


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