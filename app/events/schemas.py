import datetime
from pydantic import BaseModel


class EventCreate(BaseModel):
    name: str
    description: str
    event_time: datetime.datetime
    total_tickets: int


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    event_time: datetime.datetime | None = None
    total_tickets: int | None = None


class EventRead(BaseModel):
    id: int
    name: str
    description: str
    event_time: datetime.datetime
    total_tickets: int
    available_tickets: int
    manager_id: int

    class Config:
        from_attributes = True 