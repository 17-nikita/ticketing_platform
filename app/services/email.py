from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
from app.tickets.models import Ticket
from app.events.models import Event
from datetime import datetime


#FastMail is main class used to send emails
#  Creates a connection using your SMTP server settings
# Sends email messages

# --- Setup the ConnectionConfig using SMTP server settings---
conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_STARTTLS = settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

fm = FastMail(conf)

async def send_otp_email(email_to: str, otp: str):
    subject = "Your Verification Code"
    body = f"""
    <p>Thank you for registering.</p>
    <p>Your OTP code is: <strong>{otp}</strong></p>
    <p>This code will expire in 10 minutes.</p>
    """
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    await fm.send_message(message)


async def send_welcome_email(email_to: str):
    """
    Sends the "Registration Successful" welcome email.
    """
    subject = "Welcome! Your Registration is Successful"
    body = """
    <p>Welcome to the Ticketing Platform!</p>
    <p>Your account has been successfully verified and is now active.</p>
    <p>You can now log in and start browsing events.</p>
    """
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    
    await fm.send_message(message)


async def send_ticket_confirmation(email_to: str, ticket: Ticket, event: Event):
    subject = f"Your Ticket for {event.name}!"
    body = f"""
    <p>Hi {email_to},</p>
    <p>Your purchase is confirmed! Here are your ticket details:</p>
    
    <h3>Event: {event.name}</h3>
    <ul>
        <li><strong>Date:</strong> {event.event_time.strftime('%A, %B %d, %Y at %I:%M %p')}</li>
        <li><strong>Description:</strong> {event.description}</li>
    </ul>
    
    <h3>Your Ticket Code: <strong>{ticket.confirmation_code}</strong></h3>
    <p>This code was purchased on {ticket.purchase_time.strftime('%B %d, %Y')}.</p>
    
    <p>Thank you for using the Ticketing Platform!</p>
    """
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    
    await fm.send_message(message)




async def send_reminder_email(email_to: str, event_name: str, event_time: datetime, ticket_code: str):
    subject = f"Reminder: {event_name} is tomorrow!"
    
    # Format the time nicely
    formatted_time = event_time.strftime('%A, %B %d at %I:%M %p')

    body = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2>Event Reminder ⏰</h2>
        <p>Hi there,</p>
        <p>This is a friendly reminder that you have a ticket for <strong>{event_name}</strong> coming up soon!</p>
        
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background-color: #f9f9f9;">
            <p><strong>📅 Event:</strong> {event_name}</p>
            <p><strong>🕒 Time:</strong> {formatted_time}</p>
            <p><strong>🎟️ Ticket Code:</strong> <span style="font-size: 1.2em; font-weight: bold;">{ticket_code}</span></p>
        </div>

        <p>Please have your ticket code ready at the entrance.</p>
        <p>See you there!</p>
    </div>
    """
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=body,
        subtype="html"
    )
    
    await fm.send_message(message)