import redis.asyncio as redis
from app.core.config import settings

# Connection Pool for better performance
redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_URL, 
    encoding="utf-8", 
    decode_responses=True
)

async def get_redis():
    """Dependency for FastAPI Routers"""
    client = redis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()