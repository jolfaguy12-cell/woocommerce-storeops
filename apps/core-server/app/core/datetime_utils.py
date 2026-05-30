from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.config.settings import get_settings

try:
    import jdatetime
except ModuleNotFoundError:  # pragma: no cover - fallback keeps utilities importable before deps install.
    jdatetime = None  # type: ignore[assignment]


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp for storage in the database."""
    return datetime.now(timezone.utc)


def _as_timezone(value: datetime, timezone_name: str | None = None) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    target_timezone = ZoneInfo(timezone_name or get_settings().timezone)
    return value.astimezone(target_timezone)


def format_datetime_gregorian(value: datetime, timezone_name: str | None = None) -> str:
    localized = _as_timezone(value, timezone_name)
    return localized.strftime("%Y-%m-%d %H:%M:%S %Z")


def format_datetime_jalali(value: datetime, timezone_name: str | None = None) -> str:
    localized = _as_timezone(value, timezone_name)
    if jdatetime is None:
        return format_datetime_gregorian(value, timezone_name)
    jalali = jdatetime.datetime.fromgregorian(datetime=localized)
    return jalali.strftime("%Y/%m/%d %H:%M:%S")


def format_date_for_user(value: datetime, mode: str | None = None, timezone_name: str | None = None) -> str:
    display_mode = (mode or get_settings().date_display_mode).lower()
    if display_mode == "jalali":
        return format_datetime_jalali(value, timezone_name)
    return format_datetime_gregorian(value, timezone_name)


def format_date_for_report(value: datetime, mode: str | None = None, timezone_name: str | None = None) -> str:
    return format_date_for_user(value, mode, timezone_name)


def format_date_for_telegram(value: datetime, mode: str | None = None, timezone_name: str | None = None) -> str:
    return format_date_for_user(value, mode, timezone_name)
