from celery import Celery
from app.core.config import settings

# Initialize Celery
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Optimize configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True
)

# --- THE FIX ---
# Instead of strict imports, we tell Celery:
# "Look inside the 'app.worker' package for a file named 'tasks.py'"
celery_app.autodiscover_tasks(['app.worker'])