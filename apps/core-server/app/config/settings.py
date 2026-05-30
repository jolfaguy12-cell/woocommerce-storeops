from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "WooCommerce StoreOps"
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")
    api_prefix: str = "/api/v1"
    secret_key: str = Field(default="change-me", validation_alias="SECRET_KEY")
    access_token_expire_minutes: int = 60

    database_url: str = Field(default="postgresql+psycopg://storeops:storeops@postgres:5432/storeops", validation_alias="DATABASE_URL")
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
