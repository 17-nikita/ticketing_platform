# in: main.py
from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.database import engine, Base
from fastapi import status
from routers import auth_routers, users_routers, events_routers, tickets_routers, webhooks_routers,payment_ui_router
import logging
from app.core.throttling import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from app.worker.config import scheduler
from app.worker.tasks import send_event_reminders, close_expired_events 
from contextlib import asynccontextmanager
import sentry_sdk
from app.core.exceptions import CustomError, custom_error_handler
from app.core.logging_config import configure_logging
from routers import cart_routers
from fastapi.middleware.cors import CORSMiddleware

sentry_sdk.init(
    dsn="https://8b597a8a5b9b6c91574488f5f6c6ee8d@o4510430683201536.ingest.us.sentry.io/4510430711185408",
    send_default_pii=True,
    #debug=True,
    traces_sample_rate=1.0,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Starting... Initializing Worker.") 
    scheduler.start()  
    scheduler.add_job(send_event_reminders, "interval", minutes=60)  # runs per hour
    scheduler.add_job(close_expired_events, "interval", minutes=10)  # runs every 10 mins
    print("Startup: Running immediate cleanup check...")
    try:
        await close_expired_events()
        await send_event_reminders()
    except Exception as e:
        print(f"Startup cleanup failed: {e}")
    yield  
    print("App Stopping... Shutting down Worker.")
    scheduler.shutdown()


configure_logging()

# 2. Get the logger (It is now configured!)
logger = logging.getLogger("ticket_app")

app = FastAPI(title="Ticketing Platform API",lifespan=lifespan)

origins = [
    # "http://localhost:5173",  # The URL your Frontend is running on
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_exception_handler(CustomError, custom_error_handler)



app.include_router(auth_routers.router)
app.include_router(users_routers.router)
app.include_router(events_routers.router)
app.include_router(tickets_routers.router)
app.include_router(cart_routers.router)
app.include_router(webhooks_routers.router)
app.include_router(payment_ui_router.router)



@app.get("/")
def read_root():
    return {"Hello": "World"}

# @app.get("/sentry-debug")
# async def trigger_error():
#     # 2. This will intentionally crash the app
#     try:
#         division_by_zero = 1 / 0
#     except Exception as e:
#         sentry_sdk.capture_exception(e)
#         print("0 divisio....")
