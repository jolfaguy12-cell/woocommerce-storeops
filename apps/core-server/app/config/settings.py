from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "WooCommerce StoreOps"
    app_host: str = Field(default="127.0.0.1", validation_alias="APP_HOST")
    app_port: int = Field(default=8088, validation_alias="APP_PORT")
    environment: str = Field(default="production", validation_alias="ENVIRONMENT")
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = 60

    database_url: str = Field(default="postgresql+psycopg://storeops:storeops_password@postgres:5432/storeops", validation_alias="DATABASE_URL")
    redis_url: str = Field(default="redis://redis:6379/0", validation_alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://redis:6379/1", validation_alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://redis:6379/2", validation_alias="CELERY_RESULT_BACKEND")

    wordpress_api_key: str = Field(default="change-me", validation_alias="WORDPRESS_API_KEY")
    wordpress_hmac_secret: str = Field(default="change-me", validation_alias="WORDPRESS_HMAC_SECRET")
    hmac_timestamp_tolerance_seconds: int = 300
    reject_insecure_http: bool = Field(default=False, validation_alias="REJECT_INSECURE_HTTP")

    inventory_low_stock_threshold: int = 2
    inventory_old_oos_days: int = 30
    inventory_full_scan_cron: str = "0 3 * * *"
    inventory_fast_scan_interval_seconds: int = 60

    date_display_mode: str = Field(default="jalali", validation_alias="DATE_DISPLAY_MODE")
    timezone: str = Field(default="Asia/Tehran", validation_alias="TIMEZONE")

    telegram_enabled: bool = False
    telegram_bot_token: str | None = None
    telegram_warehouse_chat_id: str | None = None

    log_level: str = "INFO"
    log_file: str = "app/logs/storeops.log"

    @field_validator("reject_insecure_http")
    @classmethod
    def force_https_in_production(cls, value: bool, info):
        env = info.data.get("environment")
        return True if env == "production" else value


@lru_cache
def get_settings() -> Settings:
    return Settings()
