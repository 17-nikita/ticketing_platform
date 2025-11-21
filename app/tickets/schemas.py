import datetime
from pydantic import BaseModel


# We need a nested schema to show Event details inside the Ticket
class TicketEventSummary(BaseModel):
    id: int
    name: str
    event_time: datetime.datetime
    
    class Config:
        from_attributes = True

class TicketRead(BaseModel):
    id: int
    confirmation_code: str
    purchase_time: datetime.datetime
    event: TicketEventSummary 

    class Config:
        from_attributes = True