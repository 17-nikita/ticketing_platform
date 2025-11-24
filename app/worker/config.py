from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Create the scheduler instance
# We define it here so we can import 'scheduler' in main.py to start it
scheduler = AsyncIOScheduler()