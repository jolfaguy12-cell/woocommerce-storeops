import logging
from logging.config import fileConfig
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.exc import OperationalError

from app.config.settings import get_settings
from app.db.session import Base
from app.modules.inventory import models as inventory_models  # noqa: F401
from app.modules.users import models as user_models  # noqa: F401

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("storeops.alembic")
target_metadata = Base.metadata


def mask_url(url: str) -> str:
    parts = urlsplit(url)
    netloc = parts.netloc
    if "@" in netloc:
        credentials, host = netloc.rsplit("@", 1)
        username = unquote(credentials.split(":", 1)[0]) if credentials else ""
        netloc = f"{quote(username)}:***@{host}" if username else f"***@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def database_failure_guidance() -> str:
    return (
        "Database connection failed while running Alembic. Check DATABASE_URL, confirm PostgreSQL is running, "
        "and use host 'postgres' only inside Docker Compose; use '127.0.0.1' or 'localhost' when running Alembic directly on the server. "
        "Run `python3 scripts/check_db.py` from the repository root for a guided connectivity check."
    )


def run_migrations_offline() -> None:
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    except OperationalError:
        logger.error("%s DATABASE_URL=%s", database_failure_guidance(), mask_url(settings.database_url))
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
