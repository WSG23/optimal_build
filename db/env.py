"""Alembic environment configuration for Regstack."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from core.canonical_models import RegstackBase

CONFIG = context.config
if CONFIG.config_file_name is not None:
    fileConfig(CONFIG.config_file_name)

target_metadata = RegstackBase.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    url = CONFIG.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        CONFIG.get_section(CONFIG.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
