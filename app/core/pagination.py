from fastapi import Query
from typing import Generic, TypeVar, List
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

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
    total_items: int    
    total_pages: int    
    current_page: int   
    limit: int          
    items: List[T]      


async def paginate(db:AsyncSession,query,params:PaginationParams,ResponseSchema):
    # query- raw query
    # params- page,limit,offset
    # responseschema- obj of PaginationResponse 

    # count total item(total rows)
    count_query= select(func.count()).select_from(query.subquery())
    total_items= await db.scalar(count_query) or 0

    # calculate total  pages # Example: 45 items / 10 limit = 4.5 -> rounds up to 5 pages
    total_pages= ceil(total_items/params.limit)

    # Fetch the Data
    paginated_query= query.limit(params.limit).offset(params.offset)
    result= await db.execute(paginated_query)
    items= result.scalars().all()

    return {
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": params.page,
        "limit": params.limit,
        "items": items
    }