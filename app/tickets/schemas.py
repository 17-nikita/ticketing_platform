import datetime
from pydantic import BaseModel

class TicketRead(BaseModel):
    id: int
    confirmation_code: str
    purchase_time: datetime.datetime
    user_id: int
    event_id: int

    class Config:
        from_attributes = True # Pydantic v2