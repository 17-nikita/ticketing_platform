from logging.config import fileConfig
import asyncio
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context
import sys
import os


sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings 
from app.core.database import Base    
from app.core.database import engine as async_engine

# Import all of your models so Alembic can see them
from app.users.models import User
from app.events.models import Event
from app.tickets.models import Ticket


config = context.config


config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata


# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    ...
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata, 
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# --- CHANGE 2: COMMENT OUT THIS ENTIRE FUNCTION ---
# This is the old, synchronous function. We don't need it.
# def run_migrations_online() -> None:
#     """Run migrations in 'online' mode.
# 
#     In this scenario we need to create an Engine
#     and associate a connection with the context.
# 
#     """
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )
# 
#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection, target_metadata=target_metadata
#         )
# 
#         with context.begin_transaction():
#             context.run_migrations()
# --------------------------------------------------


# --- CHANGE 3: ADD THE ASYNC RUN LOGIC ---
# This is the new logic for running in async mode.

def do_run_migrations(connection: Connection) -> None:
    """
    Helper function to run the migrations in a synchronous context.
    """
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode using the app's async engine.
    """
    
    # We use our app's imported async_engine
    connectable = async_engine

    async with connectable.connect() as connection:
        # We run the synchronous 'do_run_migrations' helper
        await connection.run_sync(do_run_migrations)

    # Dispose of the engine connection
    await connectable.dispose()
# -------------------------------------------


# --- CHANGE 4: UPDATE THE FINAL 'else' BLOCK ---
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
