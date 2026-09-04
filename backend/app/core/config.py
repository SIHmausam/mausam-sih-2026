from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mausam API"
    debug: bool = True

    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    email_verification_code_expire_minutes: int = 15
    email_verification_resend_cooldown_seconds: int = 60
    email_verification_max_attempts: int = 5

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "Mausam"
    smtp_use_tls: bool = True

    email_delivery_enabled: bool = False

    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    open_meteo_weather_url: str = "https://api.open-meteo.com/v1/forecast"

    open_meteo_air_quality_url: str = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
    )
    sachet_rss_url: str
    sachet_cap_url: str

    ml_service_url: str = "http://127.0.0.1:8001"

    ml_request_timeout_seconds: float = 5.0

    push_notifications_enabled: bool = False

    firebase_project_id: str | None = None

    firebase_credentials_path: str | None = None

    notification_scheduler_enabled: bool = False

    notification_scheduler_interval_seconds: int = 900

    notification_scheduler_batch_size: int = 100

    notification_daily_summary_start_hour: int = 6

    notification_daily_summary_end_hour: int = 10


settings = Settings()
