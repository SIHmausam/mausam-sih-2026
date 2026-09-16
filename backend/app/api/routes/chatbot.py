from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.redis import get_redis
from app.dependencies.auth import get_current_user
from app.dependencies.providers import (
    get_air_quality_provider,
    get_weather_provider,
)
from app.integrations.air_quality.open_meteo import (
    OpenMeteoAirQualityProvider,
)
from app.integrations.llm.gemini_client import GeminiClient
from app.integrations.llm.groq_client import GroqClient
from app.integrations.llm.llm_provider import FallbackLLMProvider
from app.integrations.weather.open_meteo import (
    OpenMeteoWeatherProvider,
)
from app.models.user import User
from app.schemas.chatbot import (
    ChatbotRequest,
    ChatbotResponse,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.chatbot_service import (
    ChatbotService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)
from app.services.weather_service import (
    WeatherService,
)

router = APIRouter(
    prefix="/chatbot",
    tags=["Chatbot"],
)


@router.post(
    "/ask",
    response_model=ChatbotResponse,
)
async def ask_chatbot(
    payload: ChatbotRequest,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
    redis: Annotated[
        Redis,
        Depends(get_redis),
    ],
    weather_provider: Annotated[
        OpenMeteoWeatherProvider,
        Depends(get_weather_provider),
    ],
    air_quality_provider: Annotated[
        OpenMeteoAirQualityProvider,
        Depends(get_air_quality_provider),
    ],
):
    if (payload.latitude is None) != (
        payload.longitude is None
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "latitude and longitude must be provided together"
            ),
        )

    weather_context = None

    if (
        payload.latitude is not None
        and payload.longitude is not None
    ):
        weather_service = WeatherService(
            provider=weather_provider,
            redis=redis,
        )

        air_quality_service = AirQualityService(
            provider=air_quality_provider,
            redis=redis,
        )

        context_service = WeatherContextService(
            weather_service=weather_service,
            air_quality_service=air_quality_service,
        )

        try:
            weather_context = await context_service.get_context(
                payload.latitude,
                payload.longitude,
            )
        except Exception:  # noqa: BLE001
            weather_context = None

    try:
        groq_client = GroqClient()
        gemini_client = GeminiClient()


        llm_client = FallbackLLMProvider(
            primary=groq_client,
            secondary=gemini_client,
        )

        service = ChatbotService(
            redis=redis,
            llm_client=llm_client,
        )

        (
            answer,
            _questions_used,
            _questions_remaining,
        ) = await service.ask(
            user_id=str(current_user.id),
            session_id=payload.session_id,
            question=payload.question,
            weather_context=weather_context,
        )

        return ChatbotResponse(
            answer=answer,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Mausam chatbot is currently unavailable",
        ) from exc