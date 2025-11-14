from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_time = Column(DateTime, nullable=False)
    
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    
    manager_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    manager = relationship("User", back_populates="events_managed")
    tickets = relationship("Ticket", back_populates="event")