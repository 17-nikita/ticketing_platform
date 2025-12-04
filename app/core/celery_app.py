from celery import Celery
from app.core.config import settings
from celery.schedules import crontab

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



# ... existing celery config ...

celery_app.conf.beat_schedule = {
    'send-event-reminders-every-hour': {
        'task': 'send_event_reminders',  # Matches the name in tasks.py
        'schedule': crontab(minute=0),   # Run at the top of every hour
    },
    'close-expired-events-every-10-mins': {
        'task': 'close_expired_events',
        'schedule': crontab(minute='*/10'), # Run every 10 mins
    },
}
# --- THE FIX ---
# Instead of strict imports, we tell Celery:
# "Look inside the 'app.worker' package for a file named 'tasks.py'"
celery_app.autodiscover_tasks(['app.worker'])