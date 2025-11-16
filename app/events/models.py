# in: app/events/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship # <-- Import
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    
    # This is the DB-level link to a user
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # This links back to the User's 'events_managed' list.
    manager = relationship("User", back_populates="events_managed")
    

    # This links to the Ticket's 'event' property.
    tickets = relationship("Ticket", back_populates="event")