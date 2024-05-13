import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, MetaData
from sqlalchemy import pool

from app import models  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata: list[MetaData] | MetaData = [models.Base.metadata]

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
env_files = ['.env', '.env.local']
for env_file in env_files:
    env_file = Path(__file__).resolve().parent.parent.joinpath(env_file)
    print(env_file)
    load_dotenv(env_file, override=True)

section = config.config_ini_section
# config.set_section_option(section, "POSTGRES_DSN", os.environ.get("POSTGRES_DSN"))
config.set_section_option(section, "MYSQL_DSN", os.environ.get("MYSQL_DSN"))


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    print(f"开始离线模式: {url}")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_name=include_name,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def include_name(name, type_, parent_names):
    if type_ == "table":
        if isinstance(target_metadata, list):
            return any([name in item.tables for item in target_metadata])
        return name in target_metadata.tables
    else:
        return True


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    print(config.get_section("alembic"))
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            arget_metadata=target_metadata,
            include_schemas=True,
            include_name=include_name
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
