import uuid
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import (
    CardType,
)
from app.integrations.personalization.base import (
    PersonalizationProviderUnavailableError,
)
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.schemas.personalization import (
    MLPersonalizationResponse,
)
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
    WeatherContextResponse,
)
from app.services.personalization_service import (
    PersonalizationLocationNotFoundError,
    PersonalizationPersonaMissingError,
    PersonalizationPreferencesNotFoundError,
    PersonalizationService,
)


def build_context():
    return WeatherContextResponse(
        latitude=28.6139,
        longitude=77.2090,
        current=CurrentWeatherResponse(
            latitude=28.6139,
            longitude=77.2090,
            observed_at=datetime.fromisoformat("2026-09-01T17:00:00"),
            temperature=32.0,
            apparent_temperature=35.0,
            humidity=65.0,
            precipitation=0.0,
            rain=0.0,
            weather_code=1,
            wind_speed=12.0,
            is_daylight=True,
        ),
        hourly=[],
        daily=[
            DailyWeatherItem(
                date="2026-09-01",
                sunrise=datetime.fromisoformat("2026-09-01T06:00:00"),
                sunset=datetime.fromisoformat("2026-09-01T18:30:00"),
            )
        ],
        agriculture=(
            AgricultureContextResponse(
                latitude=28.6139,
                longitude=77.2090,
                surface_soil_moisture=0.31,
            )
        ),
        air_quality=(
            CurrentAirQualityResponse(
                latitude=28.6139,
                longitude=77.2090,
                us_aqi=82.0,
                european_aqi=51.0,
                uv_index=6.0,
                pm2_5=23.0,
                pm10=40.0,
                nitrogen_dioxide=12.0,
                sulphur_dioxide=5.0,
                carbon_monoxide=280.0,
                ozone=70.0,
            )
        ),
    )


def build_ml_response():
    cards = [
        "rain",
        "aqi",
        "temperature",
        "humidity",
        "uv",
        "wind",
        "soil_moisture",
        "weather_condition",
    ]

    return MLPersonalizationResponse(
        city="Delhi",
        persona="farmer",
        cards=[
            {
                "rank": index,
                "card": card,
                "score": (1.0 - index * 0.05),
                "insight": "Test insight",
            }
            for index, card in enumerate(
                cards,
                start=1,
            )
        ],
    )


def create_service(
    session,
):
    weather_context_service = AsyncMock()

    provider = AsyncMock()

    service = PersonalizationService(
        session=session,
        weather_context_service=(weather_context_service),
        personalization_provider=provider,
    )

    service.preference_repository = AsyncMock()

    service.location_repository = AsyncMock()

    return (
        service,
        weather_context_service,
        provider,
    )


@pytest.mark.asyncio
async def test_personalization_uses_ml(
    session,
):
    (
        service,
        weather_service,
        provider,
    ) = create_service(session)

    user_id = uuid.uuid4()
    location_id = uuid.uuid4()

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="farmer",
        personalized_homepage_enabled=True,
    )

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=location_id,
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )

    weather_service.get_context.return_value = build_context()

    provider.personalize.return_value = build_ml_response()

    result = await service.personalize(
        user_id=user_id,
    )

    assert result.source == "ml"

    assert result.persona == "farmer"

    assert result.cards[0].card == (CardType.RAINFALL)

    provider.personalize.assert_awaited_once()


@pytest.mark.asyncio
async def test_ml_failure_uses_fallback(
    session,
):
    (
        service,
        weather_service,
        provider,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="health",
        personalized_homepage_enabled=True,
    )

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )

    weather_service.get_context.return_value = build_context()

    provider.personalize.side_effect = PersonalizationProviderUnavailableError(
        "ML unavailable"
    )

    result = await service.personalize(
        user_id=uuid.uuid4(),
    )

    assert result.source == "fallback"

    assert result.cards[0].card == (CardType.AQI)


@pytest.mark.asyncio
async def test_missing_ml_feature_uses_fallback(
    session,
):
    (
        service,
        weather_service,
        provider,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="farmer",
        personalized_homepage_enabled=True,
    )

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )

    context = build_context()

    context.air_quality = None

    weather_service.get_context.return_value = context

    result = await service.personalize(
        user_id=uuid.uuid4(),
    )

    assert result.source == "fallback"

    provider.personalize.assert_not_awaited()


@pytest.mark.asyncio
async def test_disabled_personalization_skips_ml(
    session,
):
    (
        service,
        weather_service,
        provider,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="traveller",
        personalized_homepage_enabled=False,
    )

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )

    result = await service.personalize(
        user_id=uuid.uuid4(),
    )

    assert result.source == "fallback"

    weather_service.get_context.assert_not_awaited()

    provider.personalize.assert_not_awaited()


@pytest.mark.asyncio
async def test_missing_preferences_raises(
    session,
):
    (
        service,
        _,
        _,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = None

    with pytest.raises(PersonalizationPreferencesNotFoundError):
        await service.personalize(
            user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_missing_persona_raises(
    session,
):
    (
        service,
        _,
        _,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona=None,
        personalized_homepage_enabled=True,
    )

    with pytest.raises(PersonalizationPersonaMissingError):
        await service.personalize(
            user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_missing_primary_location_raises(
    session,
):
    (
        service,
        _,
        _,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="health",
        personalized_homepage_enabled=True,
    )

    service.location_repository.get_primary_for_user.return_value = None

    with pytest.raises(PersonalizationLocationNotFoundError):
        await service.personalize(
            user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_specific_location_must_belong_to_user(
    session,
):
    (
        service,
        _,
        _,
    ) = create_service(session)

    service.preference_repository.get_preference.return_value = SimpleNamespace(
        persona="health",
        personalized_homepage_enabled=True,
    )

    service.location_repository.get_owned_location.return_value = None

    with pytest.raises(PersonalizationLocationNotFoundError):
        await service.personalize(
            user_id=uuid.uuid4(),
            location_id=uuid.uuid4(),
        )
