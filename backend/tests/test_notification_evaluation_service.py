import uuid
from unittest.mock import AsyncMock

import pytest

from app.core.enums import (
    NotificationSeverity,
    NotificationType,
)
from app.schemas.alert import OfficialAlert
from app.services.notification_evaluation_service import (
    NotificationEvaluationService,
)


class FakePreference:
    def __init__(
        self,
        *,
        official_alerts_enabled: bool,
    ):
        self.official_alerts_enabled = official_alerts_enabled


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
