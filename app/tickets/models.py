# in: app/tickets/models.py
import datetime
import uuid
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship # <-- Import
from app.core.database import Base

def generate_confirmation_code():
    return str(uuid.uuid4().hex[:7].upper())

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    confirmation_code = Column(String, unique=True, index=True, default=generate_confirmation_code)
    purchase_time = Column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.UTC))
    
    # This is the DB-level link to a user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # This is the DB-level link to an event
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)

    # This links back to the User's 'tickets' list.
    owner = relationship("User", back_populates="tickets")
   
    # This links back to the Event's 'tickets' list.
    event = relationship("Event", back_populates="tickets")