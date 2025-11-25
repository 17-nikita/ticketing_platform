
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from app.core.database import Base
from app.users.enums import UserRole
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False) 
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp_code = Column(String, nullable=True) 
    otp_expires_at = Column(DateTime(timezone=True), nullable=True)

    
    events_managed = relationship("Event", back_populates="manager",cascade="all, delete-orphan")
    tickets = relationship("Ticket", back_populates="owner",cascade="all, delete-orphan")