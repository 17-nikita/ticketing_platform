from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

def generate_confirmation_code():
    """Generates a simple unique code."""
    return str(uuid.uuid4()).split('-')[0].upper()

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    confirmation_code = Column(String, unique=True, index=True, default=generate_confirmation_code)
    purchase_time = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    # Relationships
    owner = relationship("User", back_populates="tickets")
    event = relationship("Event", back_populates="tickets")