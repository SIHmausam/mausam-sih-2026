from typing import Annotated

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_session
from app.core.redis import get_redis
from app.integrations.air_quality.base import (
    AirQualityProvider,
)
from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.alerts.base import (
    AlertProvider,
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
from app.integrations.weather.base import (
    WeatherProvider,
)
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.alert_service import (
    AlertService,
)
from app.services.homepage_service import (
    HomepageService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)
from app.services.weather_service import (
    WeatherService,
)


def get_personalization_provider() -> PersonalizationProvider:
    return MLAPIPersonalizationProvider(
        base_url=settings.ml_service_url,
        timeout_seconds=(settings.ml_request_timeout_seconds),
    )


def get_weather_provider() -> WeatherProvider:
    return OpenMeteoWeatherProvider()


def get_air_quality_provider() -> AirQualityProvider:
    return OpenMeteoAirQualityProvider()


def get_alert_provider() -> AlertProvider:
    return SachetAlertProvider()


def get_homepage_service(
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    weather_provider: Annotated[
        WeatherProvider,
        Depends(get_weather_provider),
    ],
    air_quality_provider: Annotated[
        AirQualityProvider,
        Depends(get_air_quality_provider),
    ],
    alert_provider: Annotated[
        AlertProvider,
        Depends(get_alert_provider),
    ],
    personalization_provider: Annotated[
        PersonalizationProvider,
        Depends(get_personalization_provider),
    ],
) -> HomepageService:
    weather_service = WeatherService(
        provider=weather_provider,
        redis=redis,
    )

    air_quality_service = AirQualityService(
        provider=air_quality_provider,
        redis=redis,
    )

    weather_context_service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=(air_quality_service),
    )

    alert_service = AlertService(
        provider=alert_provider,
        redis=redis,
    )

    return HomepageService(
        session=session,
        weather_context_service=(weather_context_service),
        alert_service=alert_service,
        personalization_provider=(personalization_provider),
    )
