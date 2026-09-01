import uuid
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import (
    CardType,
)
from app.schemas.air_quality import (
    CurrentAirQualityResponse,
)
from app.schemas.alert import OfficialAlert
from app.schemas.personalization import (
    PersonalizationResult,
    PersonalizedCard,
)
from app.schemas.routine import (
    MyDayResponse,
)
from app.schemas.weather import (
    AgricultureContextResponse,
    CurrentWeatherResponse,
    DailyWeatherItem,
    WeatherContextResponse,
)
from app.services.homepage_service import (
    HomepageLocationNotFoundError,
    HomepageService,
)


def today_utc():
    return datetime.now(UTC).date()


def build_context():
    return WeatherContextResponse(
        latitude=28.6139,
        longitude=77.2090,
        current=CurrentWeatherResponse(
            latitude=28.6139,
            longitude=77.2090,
            observed_at=datetime.now(UTC),
            temperature=32.0,
            apparent_temperature=35.0,
            humidity=65.0,
            precipitation=0.0,
            rain=0.0,
            weather_code=1,
            wind_speed=10.0,
            is_daylight=True,
        ),
        hourly=[],
        daily=[
            DailyWeatherItem(
                date=today_utc().isoformat(),
                temperature_max=34.0,
                temperature_min=25.0,
            ),
        ],
        agriculture=(
            AgricultureContextResponse(
                latitude=28.6139,
                longitude=77.2090,
                surface_soil_moisture=0.3,
            )
        ),
        air_quality=(
            CurrentAirQualityResponse(
                latitude=28.6139,
                longitude=77.2090,
                aqi=80,
                aqi_standard="us",
                us_aqi=80,
                european_aqi=50,
                uv_index=5,
            )
        ),
    )


def build_personalization():
    cards = list(CardType)

    return PersonalizationResult(
        location_id=str(uuid.uuid4()),
        city="Delhi",
        persona="health",
        source="ml",
        cards=[
            PersonalizedCard(
                rank=index,
                card=card,
                score=0.8,
                insight="Test insight",
            )
            for index, card in enumerate(
                cards,
                start=1,
            )
        ],
    )


def create_service(
    session,
):
    weather = AsyncMock()
    alert = AsyncMock()
    provider = AsyncMock()

    service = HomepageService(
        session=session,
        weather_context_service=weather,
        alert_service=alert,
        personalization_provider=provider,
    )

    service.location_repository = AsyncMock()

    service.my_day_service = AsyncMock()

    service.personalization_service = AsyncMock()

    return (
        service,
        weather,
        alert,
    )


@pytest.mark.asyncio
async def test_homepage_combines_context(
    session,
):
    (
        service,
        weather,
        alert,
    ) = create_service(session)

    location_id = uuid.uuid4()

    location = SimpleNamespace(
        id=location_id,
        label="Home",
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        location_type="home",
    )

    service.location_repository.get_primary_for_user.return_value = location

    weather.get_context.return_value = build_context()

    alert.get_relevant_alerts.return_value = []

    service.my_day_service.get_my_day.return_value = MyDayResponse(
        date=today_utc(),
        routines=[],
    )

    service.personalization_service.personalize_with_context.return_value = (
        build_personalization()
    )

    response = await service.get_homepage(
        user_id=uuid.uuid4(),
        target_date=today_utc(),
    )

    assert response.location.id == (location_id)

    assert response.location.city == ("Delhi")

    assert response.weather.current.temperature == 32.0

    assert response.weather.air_quality.aqi == 80

    assert len(response.personalization.cards) == 8

    assert response.session_id


@pytest.mark.asyncio
async def test_severe_alert_enables_safety_override(
    session,
):
    (
        service,
        weather,
        alert,
    ) = create_service(session)

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        label="Home",
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        location_type="home",
    )

    weather.get_context.return_value = build_context()

    alert.get_relevant_alerts.return_value = [
        OfficialAlert(
            identifier="alert-1",
            event="Thunderstorm",
            severity="Severe",
            expires_at=(datetime.now(UTC) + timedelta(hours=1)),
        ),
    ]

    service.my_day_service.get_my_day.return_value = MyDayResponse(
        date=today_utc(),
        routines=[],
    )

    service.personalization_service.personalize_with_context.return_value = (
        build_personalization()
    )

    response = await service.get_homepage(
        user_id=uuid.uuid4(),
        target_date=today_utc(),
    )

    assert response.has_safety_override is True

    assert len(response.alerts) == 1


@pytest.mark.asyncio
async def test_expired_alert_is_removed(
    session,
):
    (
        service,
        weather,
        alert,
    ) = create_service(session)

    service.location_repository.get_primary_for_user.return_value = SimpleNamespace(
        id=uuid.uuid4(),
        label="Home",
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        location_type="home",
    )

    weather.get_context.return_value = build_context()

    alert.get_relevant_alerts.return_value = [
        OfficialAlert(
            identifier="expired",
            severity="Extreme",
            expires_at=(datetime.now(UTC) - timedelta(hours=1)),
        ),
    ]

    service.my_day_service.get_my_day.return_value = MyDayResponse(
        date=today_utc(),
        routines=[],
    )

    service.personalization_service.personalize_with_context.return_value = (
        build_personalization()
    )

    response = await service.get_homepage(
        user_id=uuid.uuid4(),
        target_date=today_utc(),
    )

    assert response.alerts == []

    assert response.has_safety_override is False


@pytest.mark.asyncio
async def test_specific_location_must_belong_to_user(
    session,
):
    (
        service,
        _,
        _,
    ) = create_service(session)

    service.location_repository.get_owned_location.return_value = None

    with pytest.raises(HomepageLocationNotFoundError):
        await service.get_homepage(
            user_id=uuid.uuid4(),
            target_date=today_utc(),
            location_id=uuid.uuid4(),
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

    service.location_repository.get_primary_for_user.return_value = None

    with pytest.raises(HomepageLocationNotFoundError):
        await service.get_homepage(
            user_id=uuid.uuid4(),
            target_date=today_utc(),
        )
