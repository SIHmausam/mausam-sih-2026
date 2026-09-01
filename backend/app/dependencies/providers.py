from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.alerts.sachet import (
    SachetAlertProvider,
)
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)


def get_weather_provider() -> OpenMeteoWeatherProvider:
    return OpenMeteoWeatherProvider()


def get_air_quality_provider() -> OpenMeteoAirQualityProvider:
    return OpenMeteoAirQualityProvider()


def get_alert_provider() -> SachetAlertProvider:
    return SachetAlertProvider()
