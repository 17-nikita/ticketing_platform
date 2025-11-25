from pydantic import BaseModel, ConfigDict,field_validator, field_serializer
from datetime import datetime


class TicketEventSummary(BaseModel):
    id: int
    name: str
    event_time: datetime
    description:str
    
    model_config = ConfigDict(from_attributes=True)

    @field_serializer('event_time')
    def serialize_event_time(self, dt: datetime, _info):
        return dt.strftime("%d-%m-%Y %I:%M %p")


class TicketRead(BaseModel):
    id: int
    confirmation_code: str
    purchase_time: datetime
    event: TicketEventSummary 

    model_config = ConfigDict(from_attributes=True)
    @field_serializer('purchase_time')
    def serialize_purchase_time(self, dt: datetime, _info):
        return dt.strftime("%d-%m-%Y %I:%M %p")