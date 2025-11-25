from datetime import datetime
from pydantic import BaseModel,field_validator, field_serializer


class EventCreate(BaseModel):
    name: str
    description: str
    event_time: datetime
    total_tickets: int

    @field_validator('event_time', mode='before')
    def parse_event_time(cls, value):
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%m-%Y %I:%M %p")
            except ValueError:
                return value 
        return value


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    event_time: datetime| None = None
    total_tickets: int | None = None


class EventRead(BaseModel):
    id: int
    name: str
    description: str
    event_time: datetime
    total_tickets: int
    available_tickets: int
    manager_id: int

    class Config:
        from_attributes = True 

    @field_serializer('event_time')
    def serialize_dt(self, dt: datetime, _info):
        return dt.strftime("%d-%m-%Y %I:%M %p")  # Output: "24-11-2025 02:30 PM"

