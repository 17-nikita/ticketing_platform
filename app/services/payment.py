import stripe
from app.core.config import settings

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(
    event_id: int,
    event_name: str,
    user_id: int,
    user_email: str,
    amount: float
):
    """
    Creates a Stripe Checkout Session.
    Amount is passed as float (e.g., 25.50) and converted to cents (2550).
    """
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            customer_email=user_email,
            line_items=[{
                'price_data': {
                    'currency': 'usd', # Change to 'inr' if using Indian Stripe account
                    'product_data': {
                        'name': f"Ticket: {event_name}",
                    },
                    'unit_amount': int(amount * 100), # Convert dollars to cents
                },
                'quantity': 1,
            }],
            mode='payment',
            # Redirect URLs
            success_url=f"{settings.DOMAIN}/docs", 
            cancel_url=f"{settings.DOMAIN}/docs",
            # CRITICAL: We hide the ID data here to retrieve it in the webhook
            metadata={
                "event_id": str(event_id),
                "user_id": str(user_id)
            }
        )
        return checkout_session.url
    except Exception as e:
        print(f"Stripe Error: {e}")
        return None