from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)


def get_weather_provider() -> OpenMeteoWeatherProvider:
    return OpenMeteoWeatherProvider()


def get_air_quality_provider() -> OpenMeteoAirQualityProvider:
    return OpenMeteoAirQualityProvider()
