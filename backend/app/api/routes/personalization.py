from typing import Annotated

from fastapi import APIRouter, Depends, Query
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_air_quality_provider,
    get_llm_insight_service,
    get_marine_provider,
    get_personalization_provider,
    get_weather_provider,
)
from app.integrations.air_quality.base import AirQualityProvider
from app.integrations.marine.base import (
    MarineProvider,
)
from app.integrations.personalization.base import PersonalizationProvider
from app.integrations.weather.base import WeatherProvider
from app.models.user import User
from app.schemas.personalization import (
    PersonalizationInsightsRequest,
    PersonalizationInsightsResponse,
    PersonalizationResult,
    PersonalizedCardInsight,
)
from app.services.air_quality_service import AirQualityService
from app.services.llm_insight_service import (
    LLMInsightService,
)
from app.services.marine_service import (
    MarineService,
)
from app.services.personalization_service import PersonalizationService
from app.services.weather_context_service import WeatherContextService
from app.services.weather_service import WeatherService

router = APIRouter(
    prefix="/personalization",
    tags=["personalization"],
)


@router.get(
    "",
    response_model=PersonalizationResult,
)
async def get_personalization(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    latitude: Annotated[
        float,
        Query(ge=-90, le=90),
    ],
    longitude: Annotated[
        float,
        Query(ge=-180, le=180),
    ],
    city: Annotated[str, Query(min_length=1)],
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
    marine_provider: Annotated[
        MarineProvider,
        Depends(get_marine_provider),
    ],
    personalization_provider: Annotated[
        PersonalizationProvider,
        Depends(get_personalization_provider),
    ],
):
    weather_service = WeatherService(
        provider=weather_provider,
        redis=redis,
    )

    air_quality_service = AirQualityService(
        provider=air_quality_provider,
        redis=redis,
    )

    marine_service = MarineService(
        provider=marine_provider,
        redis=redis,
    )

    weather_context_service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
        marine_service=marine_service,
    )

    context = await weather_context_service.get_context(
        latitude=latitude,
        longitude=longitude,
    )

    personalization_service = PersonalizationService(
        session=session,
        weather_context_service=weather_context_service,
        personalization_provider=personalization_provider,
    )

    return await personalization_service.personalize_at_coordinates(
        user_id=current_user.id,
        city=city,
        latitude=latitude,
        longitude=longitude,
        context=context,
    )

@router.post(
    "/insights",
    response_model=PersonalizationInsightsResponse,
)
async def get_personalization_insights(
    payload: PersonalizationInsightsRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
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
    marine_provider: Annotated[
        MarineProvider,
        Depends(get_marine_provider),
    ],
    personalization_provider: Annotated[
        PersonalizationProvider,
        Depends(get_personalization_provider),
    ],
    llm_insight_service: Annotated[
        LLMInsightService | None,
        Depends(get_llm_insight_service),
    ],
):
    weather_service = WeatherService(
        provider=weather_provider,
        redis=redis,
    )

    air_quality_service = AirQualityService(
        provider=air_quality_provider,
        redis=redis,
    )

    marine_service = MarineService(
        provider=marine_provider,
        redis=redis,
    )

    weather_context_service = WeatherContextService(
        weather_service=weather_service,
        air_quality_service=air_quality_service,
        marine_service=marine_service,
    )

    context = await weather_context_service.get_context(
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    service = PersonalizationService(
        session=session,
        weather_context_service=weather_context_service,
        personalization_provider=personalization_provider,
        llm_insight_service=llm_insight_service,
    )

    insights = await service.generate_insights_at_coordinates(
        user_id=current_user.id,
        city=payload.city,
        latitude=payload.latitude,
        longitude=payload.longitude,
        context=context,
        cards=payload.cards,
    )

    return PersonalizationInsightsResponse(
        insights=[
            PersonalizedCardInsight(
                card=item.card,
                insight=insights[item.card.value],
            )
            for item in payload.cards
            if item.card.value in insights
        ]
    )