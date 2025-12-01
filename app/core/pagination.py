from fastapi import Query
from typing import Generic, TypeVar, List
from pydantic import BaseModel


class PaginationParams:
    def __init__(self,page:int = Query(1,ge=1, description="Page Number"),limit:int = Query(10, le=100,description="Item per page")):
        self.page=page
        self.limit=limit
        self.offset = (page - 1) * limit

# T stands for "Type". It is a placeholder that lets us put 
# ANY list inside (Events, Tickets, Users) later.
T = TypeVar("T")

# schema for returning paginated response
class PaginatedResponse(BaseModel,Generic[T]):
    total_items: int    # Total rows in the database (e.g., 48)
    total_pages: int    # Total pages available (e.g., 5)
    current_page: int   # The page the user is currently on
    limit: int          # How many items per page
    items: List[T]      # The actual data (List of Events/Tickets)


