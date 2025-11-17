# in: main.py
from fastapi import FastAPI, Depends
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.database import engine, Base
from fastapi import status

# --- Corrected Router Imports ---
# Import the modules themselves
from routers import auth_routers, users_routers, events_routers, tickets_routers

app = FastAPI(title="Ticketing Platform API")

# --- Middleware (Limiter commented out) ---
# from app.core.throttling import limiter
# from slowapi.errors import RateLimitExceeded
# from slowapi.middleware import SlowAPIMiddleware
#
# app.state.limiter = limiter
# app.add_middleware(SlowAPIMiddleware)
#
# @app.exception_handler(RateLimitExceeded)
# async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
#     return JSONResponse(
#         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
#         content={"detail": f"Rate limit exceeded: {exc.detail}"}
#     )

# --- Routers ---
app.include_router(auth_routers.router)
app.include_router(users_routers.router)
app.include_router(events_routers.router)
app.include_router(tickets_routers.router)

# --- IMPORTANT ---
# You should NEVER use Base.metadata.create_all() in production.
# Use 'alembic upgrade head' to create and update your tables.

@app.get("/")
def read_root():
    return {"Hello": "World"}

# --- MOVED ---
# The "/profile" endpoint was here, but it belongs in routers/users.py
# I have moved it in the next step.