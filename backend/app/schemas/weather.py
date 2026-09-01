from datetime import datetime

from pydantic import BaseModel

from app.schemas.air_quality import CurrentAirQualityResponse


class CurrentWeatherResponse(BaseModel):
    latitude: float
    longitude: float

    observed_at: datetime | None = None

    temperature: float | None = None
    apparent_temperature: float | None = None
    humidity: float | None = None

    precipitation: float | None = None
    rain: float | None = None
    rain_probability: float | None = None

    weather_code: int | None = None
    wind_speed: float | None = None
    visibility: float | None = None

    is_daylight: bool | None = None


class HourlyWeatherItem(BaseModel):
    time: datetime

    temperature: float | None = None
    apparent_temperature: float | None = None
    humidity: float | None = None

    precipitation: float | None = None
    rain: float | None = None
    rain_probability: float | None = None

    weather_code: int | None = None
    wind_speed: float | None = None
    visibility: float | None = None


class HourlyWeatherResponse(BaseModel):
    latitude: float
    longitude: float

    hourly: list[HourlyWeatherItem]


class DailyWeatherItem(BaseModel):
    date: str

    weather_code: int | None = None

    temperature_max: float | None = None
    temperature_min: float | None = None

    apparent_temperature_max: float | None = None
    apparent_temperature_min: float | None = None

    sunrise: datetime | None = None
    sunset: datetime | None = None

    precipitation_sum: float | None = None
    rain_sum: float | None = None
    rain_probability_max: float | None = None

    wind_speed_max: float | None = None


class DailyWeatherResponse(BaseModel):
    latitude: float
    longitude: float

    daily: list[DailyWeatherItem]


class AgricultureContextResponse(BaseModel):
    latitude: float
    longitude: float

    surface_soil_moisture: float | None = None
    evapotranspiration: float | None = None
    vapour_pressure_deficit: float | None = None


class WeatherContextResponse(BaseModel):
    latitude: float
    longitude: float

    current: CurrentWeatherResponse
    hourly: list[HourlyWeatherItem]
    daily: list[DailyWeatherItem]

    agriculture: AgricultureContextResponse | None = None

    air_quality: CurrentAirQualityResponse | None = None
