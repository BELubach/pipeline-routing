from logging.config import fileConfig
import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add the parent directory to the path to import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
# for 'autogenerate' support
target_metadata = Base.metadata

SPRING_BATCH_TABLES = {
    "batch_job_execution",
    "batch_job_execution_context",
    "batch_job_execution_params",
    "batch_job_instance",
    "batch_step_execution",
    "batch_step_execution_context",
}

SPRING_BATCH_PREFIXES = (
    "batch_job_",
    "batch_step_",
    "job_exec_",
    "job_inst_",
    "step_exec_",
)


def should_skip_object(name, type_):
    if not name:
        return False

    if type_ == "table" and name in SPRING_BATCH_TABLES:
        return True

    if type_ in {"index", "sequence", "table", "primary_key_constraint", "foreign_key_constraint", "unique_constraint"}:
        return name.startswith(SPRING_BATCH_PREFIXES)

    return False


def include_object(object, name, type_, reflected, compare_to):
    """
    Skip PostGIS/system tables and externally managed Spring Batch objects.
    """
    if should_skip_object(name, type_):
        return False

    if type_ == "table":
        if name in ("spatial_ref_sys", "topology", "layer"):
            return False
        if hasattr(object, "schema") and object.schema in ("topology", "tiger", "tiger_data"):
            return False
    return True

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,  # <--- add here
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,  # <--- add here
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()