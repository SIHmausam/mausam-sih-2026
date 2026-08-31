from datetime import datetime

from pydantic import BaseModel


class CurrentAirQualityResponse(BaseModel):
    latitude: float
    longitude: float

    # Normalized AQI used by the application.
    aqi: float | None = None
    aqi_standard: str | None = None

    # Kept because the current ML model
    # explicitly consumes both.
    us_aqi: float | None = None
    european_aqi: float | None = None

    pm2_5: float | None = None
    pm10: float | None = None

    nitrogen_dioxide: float | None = None
    sulphur_dioxide: float | None = None
    carbon_monoxide: float | None = None
    ozone: float | None = None

    uv_index: float | None = None


class HourlyAirQualityItem(BaseModel):
    time: datetime

    us_aqi: float | None = None
    european_aqi: float | None = None

    pm2_5: float | None = None
    pm10: float | None = None

    nitrogen_dioxide: float | None = None
    sulphur_dioxide: float | None = None
    carbon_monoxide: float | None = None
    ozone: float | None = None

    uv_index: float | None = None


class HourlyAirQualityResponse(BaseModel):
    latitude: float
    longitude: float

    hourly: list[HourlyAirQualityItem]
