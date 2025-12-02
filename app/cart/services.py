import json
from datetime import datetime, timedelta
from redis.asyncio import Redis

from app.core.config import settings
from app.events.models import Event
# Import the task and the helper from your tasks.py file
from app.worker.tasks import send_initial_reminder, revoke_task

class CartService:
    
    @staticmethod
    async def add_to_cart(redis: Redis, user_id: int, user_email: str, event: Event):
        """
        Adds item to Redis and schedules the 1st email reminder.
        """
        cart_key = f"cart:{user_id}"
        
        # 1. Check if Event is expired
        # Use simple datetime comparison (ensure timezone awareness in production)
        if event.event_time < datetime.now(event.event_time.tzinfo):
             return {"status": "error", "message": "Cannot add. Event has already passed."}

        # 2. Schedule the Initial Celery Task (5 Hours from now)
        # We use apply_async because we need the delay (eta).
        eta_time = datetime.utcnow() + timedelta(minutes=settings.CART_INITIAL_DELAY_MINS)
        
        # This returns a Task object immediately
        task = send_initial_reminder.apply_async(
            args=[user_id, event.id, user_email, event.name], 
            eta=eta_time
        )
        
        # 3. Save Data to Redis
        cart_item = {
            "event_id": event.id,
            "event_name": event.name,
            "price": event.ticket_price,
            "event_time": event.event_time.isoformat(),
            "added_at": datetime.utcnow().isoformat(),
            "active_task_id": task.id  # CRITICAL: Save Task ID so we can cancel it later
        }

        await redis.hset(cart_key, str(event.id), json.dumps(cart_item))
        
        return {"status": "success", "message": "Added to cart", "data": cart_item}

    @staticmethod
    async def get_cart(redis: Redis, user_id: int):
        cart_key = f"cart:{user_id}"
        raw_items = await redis.hgetall(cart_key)
        
        valid_items = []
        expired_items = []

        for event_id, item_json in raw_items.items():
            item = json.loads(item_json)
            
            # Check if event passed while it was sitting in the cart
            try:
                event_time = datetime.fromisoformat(item['event_time'])
                if event_time < datetime.now(event_time.tzinfo):
                    item['status'] = "EXPIRED"
                    expired_items.append(item)
                else:
                    item['status'] = "ACTIVE"
                    valid_items.append(item)
            except Exception:
                # Fallback if date parsing fails
                valid_items.append(item)
            
        return {"items": valid_items, "expired": expired_items}

    @staticmethod
    async def remove_from_cart(redis: Redis, user_id: int, event_id: int):
        """
        Called when user buys ticket OR removes manually.
        Stops the reminder emails immediately.
        """
        cart_key = f"cart:{user_id}"
        
        # 1. Get the item to find the active Celery Task ID
        raw_item = await redis.hget(cart_key, str(event_id))
        if raw_item:
            item = json.loads(raw_item)
            task_id = item.get("active_task_id")
            
            # 2. Kill the Celery Task
            if task_id:
                print(f"🛑 Cart Item Removed: Revoking task {task_id}")
                revoke_task(task_id)

        # 3. Delete from Redis
        await redis.hdel(cart_key, str(event_id))