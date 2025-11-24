# in: main.py
from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.database import engine, Base
from fastapi import status
from routers import auth_routers, users_routers, events_routers, tickets_routers

from app.core.throttling import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.worker.config import scheduler
from app.worker.tasks import send_event_reminders, close_expired_events 
from contextlib import asynccontextmanager



@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Starting... Initializing Worker.")  
    # Register the Task
    scheduler.add_job(send_event_reminders, "interval", minutes=60)  
    scheduler.add_job(close_expired_events, "cron", hour=0, minute=0)
    scheduler.start() 
    yield  
    print("App Stopping... Shutting down Worker.")
    scheduler.shutdown()

app = FastAPI(title="Ticketing Platform API",lifespan=lifespan)


app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



app.include_router(auth_routers.router)
app.include_router(users_routers.router)
app.include_router(events_routers.router)
app.include_router(tickets_routers.router)



@app.get("/")
def read_root():
    return {"Hello": "World"}
