from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Mausam API"
    debug: bool = True

    database_url: str

    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

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


settings = Settings()
