import uuid
from datetime import UTC, date, datetime, time
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.core.enums import RoutineImpactLevel
from app.services.my_day_service import MyDayService

TEST_USER_ID = uuid.uuid4()
TEST_LOCATION_ID = uuid.uuid4()


def make_routine(
    *,
    name: str = "Morning Run",
    days_of_week: list[str] | None = None,
    saved_location_id: uuid.UUID | None = TEST_LOCATION_ID,
    start_time: time = time(7, 0),
):
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=TEST_USER_ID,
        name=name,
        activity_context="outdoor_health",
        saved_location_id=saved_location_id,
        days_of_week=days_of_week or ["tuesday"],
        start_time=start_time,
        duration_minutes=45,
        is_enabled=True,
    )


def make_location():
    return SimpleNamespace(
        id=TEST_LOCATION_ID,
        label="Home",
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
        is_primary=True,
    )


def make_weather_context():
    current = SimpleNamespace(
        temperature=28.0,
        apparent_temperature=31.0,
        humidity=65.0,
        rain=0.0,
        rain_probability=10.0,
        wind_speed=8.0,
        visibility=10000.0,
    )

    hourly_item = SimpleNamespace(
        time=datetime(
            2026,
            9,
            1,
            7,
            0,
            tzinfo=UTC,
        ),
        temperature=27.0,
        apparent_temperature=29.0,
        humidity=68.0,
        rain=0.0,
        rain_probability=10.0,
        wind_speed=7.0,
        visibility=10000.0,
    )

    air_quality = SimpleNamespace(
        aqi=55.0,
        uv_index=2.0,
    )

    agriculture = SimpleNamespace(
        surface_soil_moisture=0.2,
    )

    return SimpleNamespace(
        current=current,
        hourly=[hourly_item],
        air_quality=air_quality,
        agriculture=agriculture,
    )


def build_service():
    service = MyDayService(
        session=AsyncMock(),
        weather_context_service=AsyncMock(),
        alert_service=AsyncMock(),
    )

    service.routine_repository = AsyncMock()
    service.location_repository = AsyncMock()

    service.weather_context_service = AsyncMock()
    service.alert_service = AsyncMock()

    return service


@pytest.mark.asyncio
async def test_my_day_returns_only_routines_for_target_weekday():
    service = build_service()

    tuesday_routine = make_routine(
        name="Tuesday Run",
        days_of_week=["tuesday"],
    )

    monday_routine = make_routine(
        name="Monday Run",
        days_of_week=["monday"],
    )

    service.routine_repository.list_enabled_for_user.return_value = [
        tuesday_routine,
        monday_routine,
    ]

    service.location_repository.get_owned_location.return_value = make_location()

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    assert len(response.routines) == 1

    assert response.routines[0].name == "Tuesday Run"


@pytest.mark.asyncio
async def test_my_day_returns_unavailable_without_location():
    service = build_service()

    routine = make_routine(
        saved_location_id=None,
    )

    service.routine_repository.list_enabled_for_user.return_value = [routine]

    service.location_repository.get_primary_for_user.return_value = None

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    assert len(response.routines) == 1

    result = response.routines[0]

    assert result.impact == RoutineImpactLevel.UNAVAILABLE

    assert result.location is None
    assert result.weather is None

    service.weather_context_service.get_context.assert_not_called()

    service.alert_service.get_relevant_alerts.assert_not_called()


@pytest.mark.asyncio
async def test_my_day_uses_primary_location_as_fallback():
    service = build_service()

    routine = make_routine(
        saved_location_id=None,
    )

    location = make_location()

    service.routine_repository.list_enabled_for_user.return_value = [routine]

    service.location_repository.get_primary_for_user.return_value = location

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    result = response.routines[0]

    assert result.location is not None

    assert result.location.id == location.id

    service.location_repository.get_primary_for_user.assert_awaited_once_with(
        user_id=TEST_USER_ID
    )


@pytest.mark.asyncio
async def test_my_day_prefers_routine_saved_location():
    service = build_service()

    routine = make_routine()

    location = make_location()

    service.routine_repository.list_enabled_for_user.return_value = [routine]

    service.location_repository.get_owned_location.return_value = location

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    assert response.routines[0].location.id == location.id

    service.location_repository.get_owned_location.assert_awaited_once_with(
        location_id=routine.saved_location_id,
        user_id=TEST_USER_ID,
    )


@pytest.mark.asyncio
async def test_my_day_returns_weather_snapshot():
    service = build_service()

    routine = make_routine()

    service.routine_repository.list_enabled_for_user.return_value = [routine]

    service.location_repository.get_owned_location.return_value = make_location()

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    weather = response.routines[0].weather

    assert weather is not None

    assert weather.temperature == 27.0
    assert weather.aqi == 55.0
    assert weather.uv_index == 2.0

    assert weather.surface_soil_moisture == 0.2


@pytest.mark.asyncio
async def test_my_day_returns_safe_for_normal_conditions():
    service = build_service()

    service.routine_repository.list_enabled_for_user.return_value = [make_routine()]

    service.location_repository.get_owned_location.return_value = make_location()

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    assert response.routines[0].impact == RoutineImpactLevel.SAFE


@pytest.mark.asyncio
async def test_same_location_context_is_reused():
    service = build_service()

    first = make_routine(
        name="Morning Run",
        start_time=time(7, 0),
    )

    second = make_routine(
        name="Evening Walk",
        start_time=time(18, 0),
    )

    service.routine_repository.list_enabled_for_user.return_value = [
        first,
        second,
    ]

    service.location_repository.get_owned_location.return_value = make_location()

    service.weather_context_service.get_context.return_value = make_weather_context()

    service.alert_service.get_relevant_alerts.return_value = []

    response = await service.get_my_day(
        user_id=TEST_USER_ID,
        target_date=date(
            2026,
            9,
            1,
        ),
    )

    assert len(response.routines) == 2

    assert service.weather_context_service.get_context.await_count == 1

    assert service.alert_service.get_relevant_alerts.await_count == 1
