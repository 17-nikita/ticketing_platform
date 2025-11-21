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
    
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )

    event_id = Column(
        Integer, 
        ForeignKey("events.id", ondelete="CASCADE"), 
        nullable=False
    )
   
    owner = relationship("User", back_populates="tickets")

    event = relationship("Event", back_populates="tickets")