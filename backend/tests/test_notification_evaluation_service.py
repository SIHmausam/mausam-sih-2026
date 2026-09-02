import uuid
from datetime import date, time
from unittest.mock import AsyncMock

import pytest

from app.core.enums import (
    ActivityContext,
    NotificationSeverity,
    NotificationType,
    RoutineImpactLevel,
)
from app.schemas.alert import OfficialAlert
from app.schemas.routine import (
    MyDayResponse,
    MyDayRoutineItem,
    RoutineLocationSummary,
)
from app.services.notification_evaluation_service import (
    NotificationEvaluationService,
)


class FakePreference:
    def __init__(
        self,
        *,
        official_alerts_enabled: bool = True,
        routine_alerts_enabled: bool = True,
    ):
        self.official_alerts_enabled = official_alerts_enabled

        self.routine_alerts_enabled = routine_alerts_enabled


def severe_alert() -> OfficialAlert:
    return OfficialAlert(
        identifier="CAP-SEVERE-001",
        event="Thunderstorm",
        headline=("Severe thunderstorm warning"),
        description=("Severe thunderstorm conditions are expected."),
        instruction=("Stay indoors and avoid open areas."),
        severity="Severe",
    )


def moderate_alert() -> OfficialAlert:
    return OfficialAlert(
        identifier="CAP-MODERATE-001",
        event="Thunderstorm",
        severity="Moderate",
    )


@pytest.mark.asyncio
async def test_severe_alert_creates_notification():
    service = NotificationEvaluationService(AsyncMock())

    user_id = uuid.uuid4()
    location_id = uuid.uuid4()

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(official_alerts_enabled=True)
    )

    service.notification_service.create_notification_once = AsyncMock(
        return_value=(
            AsyncMock(),
            True,
        )
    )

    created = await service.evaluate_official_alerts(
        user_id=user_id,
        location_id=location_id,
        alerts=[severe_alert()],
    )

    assert created == 1

    (service.notification_service.create_notification_once.assert_awaited_once())

    kwargs = service.notification_service.create_notification_once.await_args.kwargs

    assert kwargs["notification_type"] == NotificationType.OFFICIAL_ALERT

    assert kwargs["severity"] == NotificationSeverity.WARNING

    assert kwargs["source"] == "sachet"

    assert kwargs["source_reference"] == "CAP-SEVERE-001"

    assert kwargs["related_location_id"] == location_id


@pytest.mark.asyncio
async def test_extreme_alert_is_critical():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(official_alerts_enabled=True)
    )

    service.notification_service.create_notification_once = AsyncMock(
        return_value=(
            AsyncMock(),
            True,
        )
    )

    alert = OfficialAlert(
        identifier="CAP-EXTREME-001",
        event="Cyclone",
        severity="Extreme",
    )

    await service.evaluate_official_alerts(
        user_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        alerts=[alert],
    )

    kwargs = service.notification_service.create_notification_once.await_args.kwargs

    assert kwargs["severity"] == NotificationSeverity.CRITICAL


@pytest.mark.asyncio
async def test_moderate_alert_does_not_create_notification():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(official_alerts_enabled=True)
    )

    service.notification_service.create_notification_once = AsyncMock()

    created = await service.evaluate_official_alerts(
        user_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        alerts=[moderate_alert()],
    )

    assert created == 0

    (service.notification_service.create_notification_once.assert_not_awaited())


@pytest.mark.asyncio
async def test_disabled_official_notifications_are_skipped():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(official_alerts_enabled=False)
    )

    service.notification_service.create_notification_once = AsyncMock()

    created = await service.evaluate_official_alerts(
        user_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        alerts=[severe_alert()],
    )

    assert created == 0

    (service.notification_service.create_notification_once.assert_not_awaited())


@pytest.mark.asyncio
async def test_missing_preferences_are_skipped():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(return_value=None)

    service.notification_service.create_notification_once = AsyncMock()

    created = await service.evaluate_official_alerts(
        user_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        alerts=[severe_alert()],
    )

    assert created == 0


def build_routine(
    *,
    impact: RoutineImpactLevel,
) -> MyDayRoutineItem:
    return MyDayRoutineItem(
        routine_id=uuid.uuid4(),
        name="Morning Run",
        activity_context=(ActivityContext.OUTDOOR_HEALTH),
        start_time=time(
            hour=6,
            minute=30,
        ),
        duration_minutes=60,
        location=RoutineLocationSummary(
            id=uuid.uuid4(),
            label="Home",
            city="Delhi",
            latitude=28.6139,
            longitude=77.2090,
        ),
        impact=impact,
        reasons=[("Air quality may be unsuitable for prolonged outdoor activity.")],
        recommendation=("Proceed carefully and review conditions before starting."),
        weather=None,
    )


@pytest.mark.asyncio
async def test_caution_routine_creates_notification():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(routine_alerts_enabled=True)
    )

    service.notification_service.create_notification_once = AsyncMock(
        return_value=(
            AsyncMock(),
            True,
        )
    )

    routine = build_routine(impact=RoutineImpactLevel.CAUTION)

    my_day = MyDayResponse(
        date=date(2026, 9, 2),
        routines=[routine],
    )

    created = await service.evaluate_routine_impacts(
        user_id=uuid.uuid4(),
        my_day=my_day,
    )

    assert created == 1

    kwargs = service.notification_service.create_notification_once.await_args.kwargs

    assert kwargs["notification_type"] == NotificationType.ROUTINE_WARNING

    assert kwargs["severity"] == NotificationSeverity.CAUTION

    assert kwargs["source"] == "my_day"

    assert kwargs["source_reference"] == (f"routine:{routine.routine_id}:2026-09-02")


@pytest.mark.asyncio
async def test_avoid_routine_uses_warning_severity():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference()
    )

    service.notification_service.create_notification_once = AsyncMock(
        return_value=(
            AsyncMock(),
            True,
        )
    )

    my_day = MyDayResponse(
        date=date(2026, 9, 2),
        routines=[build_routine(impact=RoutineImpactLevel.AVOID)],
    )

    await service.evaluate_routine_impacts(
        user_id=uuid.uuid4(),
        my_day=my_day,
    )

    kwargs = service.notification_service.create_notification_once.await_args.kwargs

    assert kwargs["severity"] == NotificationSeverity.WARNING


@pytest.mark.asyncio
async def test_safe_routine_does_not_notify():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference()
    )

    service.notification_service.create_notification_once = AsyncMock()

    my_day = MyDayResponse(
        date=date(2026, 9, 2),
        routines=[build_routine(impact=RoutineImpactLevel.SAFE)],
    )

    created = await service.evaluate_routine_impacts(
        user_id=uuid.uuid4(),
        my_day=my_day,
    )

    assert created == 0

    (service.notification_service.create_notification_once.assert_not_awaited())


@pytest.mark.asyncio
async def test_disabled_routine_notifications_are_skipped():
    service = NotificationEvaluationService(AsyncMock())

    service.preference_repository.get_preference = AsyncMock(
        return_value=FakePreference(routine_alerts_enabled=False)
    )

    service.notification_service.create_notification_once = AsyncMock()

    my_day = MyDayResponse(
        date=date(2026, 9, 2),
        routines=[build_routine(impact=RoutineImpactLevel.CAUTION)],
    )

    created = await service.evaluate_routine_impacts(
        user_id=uuid.uuid4(),
        my_day=my_day,
    )

    assert created == 0

    (service.notification_service.create_notification_once.assert_not_awaited())
