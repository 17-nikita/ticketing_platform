
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship 
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_time = Column(DateTime(timezone=True), nullable=False)
    total_tickets = Column(Integer, nullable=False)
    available_tickets = Column(Integer, nullable=False)
    status = Column(String, default="UPCOMING")
    manager_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False
    )
    # Each event is managed by one user.
    manager = relationship("User", back_populates="events_managed")
    #One event can have many tickets.
    tickets = relationship(
        "Ticket", 
        back_populates="event",
        cascade="all, delete-orphan"
    )