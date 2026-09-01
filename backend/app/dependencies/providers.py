from app.core.config import settings
from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.alerts.sachet import (
    SachetAlertProvider,
)
from app.integrations.personalization.base import (
    PersonalizationProvider,
)
from app.integrations.personalization.ml_api import (
    MLAPIPersonalizationProvider,
)
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)


def get_personalization_provider() -> PersonalizationProvider:
    return MLAPIPersonalizationProvider(
        base_url=settings.ml_service_url,
        timeout_seconds=(settings.ml_request_timeout_seconds),
    )


def get_weather_provider() -> OpenMeteoWeatherProvider:
    return OpenMeteoWeatherProvider()


def get_air_quality_provider() -> OpenMeteoAirQualityProvider:
    return OpenMeteoAirQualityProvider()


def get_alert_provider() -> SachetAlertProvider:
    return SachetAlertProvider()
