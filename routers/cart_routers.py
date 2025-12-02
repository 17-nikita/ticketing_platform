from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core import rbac
from app.users.models import User
from app.cart.services import CartService
from app.events.services import EventService

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("/add/{event_id}")
async def add_item_to_cart(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(rbac.get_current_user)
):
    # 1. Get Event Details
    event = await EventService.get_event_by_id(db, event_id)
    
    # 2. Add to Cart Service (Starts the 5-hour timer)
    result = await CartService.add_to_cart(
        redis, 
        current_user.id, 
        current_user.email, 
        event
    )
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.get("/")
async def view_my_cart(
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(rbac.get_current_user)
):
    return await CartService.get_cart(redis, current_user.id)

@router.delete("/remove/{event_id}")
async def remove_item_from_cart(
    event_id: int,
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(rbac.get_current_user)
):
    await CartService.remove_from_cart(redis, current_user.id, event_id)
    return {"message": "Item removed and reminders stopped."}