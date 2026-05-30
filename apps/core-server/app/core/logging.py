import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import structlog

from app.config.settings import get_settings

SECRET_MARKERS = ("token", "secret", "password", "api_key", "authorization")


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for marker in SECRET_MARKERS:
            if marker in message.lower():
                record.msg = "[redacted sensitive log message]"
                record.args = ()
                break
        return True


def configure_logging() -> None:
    settings = get_settings()
    Path(settings.log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    root = logging.getLogger()
    handler = RotatingFileHandler(settings.log_file, maxBytes=10_000_000, backupCount=5)
    handler.addFilter(SecretRedactionFilter())
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(handler)
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper())))
