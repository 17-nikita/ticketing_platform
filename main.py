from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.database import engine, Base
from fastapi import status
from routers import auth_routers, users_routers, events_routers, tickets_routers, webhooks_routers, payment_ui_router, cart_routers
import logging
from app.core.throttling import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler
from contextlib import asynccontextmanager
import sentry_sdk
from app.core.exceptions import CustomError, custom_error_handler
from app.core.logging_config import configure_logging
from fastapi.middleware.cors import CORSMiddleware

sentry_sdk.init(
    dsn="https://8b597a8a5b9b6c91574488f5f6c6ee8d@o4510430683201536.ingest.us.sentry.io/4510430711185408",
    send_default_pii=True,
    #debug=True,
    traces_sample_rate=1.0,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App Starting...")  
    yield   
    print("App Stopping...")


configure_logging()

# 2. Get the logger (It is now configured!)
logger = logging.getLogger("ticket_app")

app = FastAPI(title="Ticketing Platform API", lifespan=lifespan)

origins = [
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


# Router inclusions (Prefixes are handled inside the router files)
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

@app.get("/sentry-debug")
async def trigger_error():
    # 2. This will intentionally crash the app
    try:
        division_by_zero = 1 / 0
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print("0 divisio....")