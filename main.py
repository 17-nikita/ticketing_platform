

# ticketing_platform/
# ├── alembic/                      # Alembic migrations folder
# │
# ├── app/                          # Main application (LOGIC ONLY)
# │   ├── __init__.py
# │
# │   ├── core/                     # Shared, cross-cutting logic
# │   │   ├── __init__.py
# │   │   ├── config.py             # Pydantic Settings
# │   │   ├── database.py           # Engine, Sessionmaker, get_db
# │   │   ├── rbac.py               # All RBAC logic (get_current_user, etc)
# │   │   └── throttling.py         # Throttling/slowapi configuration
# │
# │   ├── auth/                     # "Auth" feature (NO router.py)
# │   │   ├── __init__.py
# │   │   ├── schemas.py            # Pydantic: Token, TokenData
# │   │   ├── hashing.py            # Passlib logic
# │   │   ├── jwt.py                # JWT creation/decoding
# │   │   └── services.py           # Logic for registration, login
# │
# │   ├── users/                    # "User" feature (NO router.py)
# │   │   ├── __init__.py
# │   │   ├── crud.py               # DB logic: get_user_by_email
# │   │   ├── models.py             # SQLAlchemy: User model
# │   │   └── schemas.py            # Pydantic: UserRead
# │
# │   ├── events/                   # "Event" feature (NO router.py)
# │   │   ├── __init__.py
# │   │   ├── crud.py               # DB logic: create_event
# │   │   ├── models.py             # SQLAlchemy: Event model
# │   │   └── schemas.py            # Pydantic: EventCreate, EventRead
# │
# │   ├── tickets/                  # "Ticket" feature (NO router.py)
# │   │   ├── __init__.py
# │   │   ├── crud.py               # DB logic: create_ticket
# │   │   ├── models.py             # SQLAlchemy: Ticket model
# │   │   └── schemas.py            # Pydantic: TicketRead
# │
# │   ├── services/                 # External service integrations
# │   │   ├── ... (email.py, sms.py)
# │
# │   ├── worker/                   # Background tasks (Cronjobs)
# │   │   |── __init__.py
# │   │   ├── config.py             # Arq worker settings
# │   │   └── tasks.py              # Task definitions
# │   │
# │
# │   
# │
# ├── routers/                      # <-- NEW FOLDER (at the same level as app)
# │   ├── __init__.py
# │   ├── auth.py                   # <-- MOVED (was app/auth/router.py)
# │   ├── users.py                  # <-- MOVED (was app/users/router.py)
# │   ├── events.py                 # <-- MOVED (was app/events/router.py)
# │   └── tickets.py                # <-- MOVED (was app/tickets/router.py)
# │
# ├── alembic.ini                   # Alembic config file
# ├── run_worker.py                 # Script to start your Arq worker
# ├── .env                          # All secrets
# ├── .gitignore
# ├── main.py                       # <-- Main file to create/run FastAPI app
# ├── requirements.txt
# └── README.md






# in: main.py
from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.database import engine, Base
from ticketing_platform.routers import auth_routers # Assuming routers is a package
from app.users import schemas
from app.core.rbac import get_current_user
from app.core.throttling import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import status
from routers import auth_routers,events_routers,tickets_routers,users_routers,tickets_routers

app = FastAPI(title="Ticketing Platform API")

# --- Middleware ---
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}"}
    )

# --- Routers ---
app.include_router(auth_routers.router)
app.include_router(users_routers.router)
app.include_router(events_routers.router)
app.include_router(tickets_routers.router)

# --- IMPORTANT ---
# I removed your on_startup event.
# You should NEVER use Base.metadata.create_all() in production.
# Use 'alembic upgrade head' to create and update your tables.

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/profile", response_model=schemas.UserRead)
async def profile(current_user = Depends(get_current_user)):
    return current_user