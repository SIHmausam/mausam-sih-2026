import uuid
from datetime import UTC, date, datetime, time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.repositories.notification_candidate_repository import (
    NotificationCandidate,
)
from app.services.notification_sweep_service import (
    NotificationSweepService,
)


def build_candidate() -> NotificationCandidate:
    return NotificationCandidate(
        user_id=uuid.uuid4(),
        location_id=uuid.uuid4(),
        city="Delhi",
        latitude=28.6139,
        longitude=77.2090,
    )


def build_context():
    return SimpleNamespace(
        current=SimpleNamespace(
            observed_at=None,
        ),
        air_quality=None,
        daily=[],
    )


def build_my_day_service_mock():
    service = AsyncMock()

    service.environment_key = Mock(
        return_value=(
            28.614,
            77.209,
            "delhi",
        )
    )

    return service


def build_my_day(
    *,
    routines=None,
):
    routine_list = list(routines or [])

    my_day = SimpleNamespace(
        date=date(2026, 9, 3),
        routines=routine_list,
    )

    def model_copy(
        *,
        update,
    ):
        return SimpleNamespace(
            date=my_day.date,
            routines=update.get(
                "routines",
                routine_list,
            ),
        )

    my_day.model_copy = Mock(side_effect=model_copy)

    return my_day


def build_routine(
    *,
    start_time: time = time(7, 0),
):
    return SimpleNamespace(
        routine_id=uuid.uuid4(),
        start_time=start_time,
    )


@pytest.mark.asyncio
async def test_candidate_runs_all_notification_evaluators():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    my_day_service.get_my_day.return_value = build_my_day()

    evaluation_service.evaluate_official_alerts.return_value = 1
    evaluation_service.evaluate_routine_impacts.return_value = 2
    evaluation_service.evaluate_environmental_conditions.return_value = 1
    evaluation_service.evaluate_daily_summary.return_value = 1

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    candidate = build_candidate()

    created = await service.evaluate_candidate(
        candidate=candidate,
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            40,
            tzinfo=UTC,
        ),
        include_daily_summary=True,
    )

    assert created == 5

    weather_service.get_context.assert_awaited_once_with(
        latitude=candidate.latitude,
        longitude=candidate.longitude,
    )

    alert_service.get_relevant_alerts.assert_awaited_once_with(
        latitude=candidate.latitude,
        longitude=candidate.longitude,
        city=candidate.city,
    )

    expected_cache = {
        (
            28.614,
            77.209,
            "delhi",
        ): (
            weather_service.get_context.return_value,
            [],
        )
    }

    my_day_service.get_my_day.assert_awaited_once_with(
        user_id=candidate.user_id,
        target_date=date(2026, 9, 3),
        context_cache=expected_cache,
    )

    (evaluation_service.evaluate_official_alerts.assert_awaited_once())

    (evaluation_service.evaluate_routine_impacts.assert_awaited_once())

    (evaluation_service.evaluate_environmental_conditions.assert_awaited_once())

    (evaluation_service.evaluate_daily_summary.assert_awaited_once())


@pytest.mark.asyncio
async def test_daily_summary_can_be_skipped():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    my_day_service.get_my_day.return_value = build_my_day()

    evaluation_service.evaluate_official_alerts.return_value = 0
    evaluation_service.evaluate_routine_impacts.return_value = 0
    evaluation_service.evaluate_environmental_conditions.return_value = 0

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    await service.evaluate_candidate(
        candidate=build_candidate(),
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            40,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    (evaluation_service.evaluate_daily_summary.assert_not_awaited())


@pytest.mark.asyncio
async def test_notification_counts_are_accumulated():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    my_day_service.get_my_day.return_value = build_my_day()

    evaluation_service.evaluate_official_alerts.return_value = 2
    evaluation_service.evaluate_routine_impacts.return_value = 1
    evaluation_service.evaluate_environmental_conditions.return_value = 2

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    created = await service.evaluate_candidate(
        candidate=build_candidate(),
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            40,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    assert created == 5


@pytest.mark.asyncio
async def test_provider_failure_propagates_from_candidate():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.side_effect = RuntimeError("weather unavailable")

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    with pytest.raises(
        RuntimeError,
        match="weather unavailable",
    ):
        await service.evaluate_candidate(
            candidate=build_candidate(),
            target_date=date(2026, 9, 3),
            current_time=datetime(
                2026,
                9,
                3,
                6,
                40,
                tzinfo=UTC,
            ),
            include_daily_summary=False,
        )


@pytest.mark.asyncio
async def test_sweep_continues_when_one_user_fails():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    first = build_candidate()
    second = build_candidate()

    service.evaluate_candidate = AsyncMock(
        side_effect=[
            RuntimeError("provider unavailable"),
            3,
        ]
    )

    result = await service.run_sweep(
        candidates=[
            first,
            second,
        ],
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            40,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    assert result.processed_users == 1
    assert result.failed_users == 1
    assert result.notifications_created == 3

    assert service.evaluate_candidate.await_count == 2


@pytest.mark.asyncio
async def test_routine_before_reminder_window_is_filtered_out():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    routine = build_routine(start_time=time(7, 0))

    my_day_service.get_my_day.return_value = build_my_day(
        routines=[routine],
    )

    evaluation_service.evaluate_official_alerts.return_value = 0
    evaluation_service.evaluate_routine_impacts.return_value = 0
    evaluation_service.evaluate_environmental_conditions.return_value = 0

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    await service.evaluate_candidate(
        candidate=build_candidate(),
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            20,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    kwargs = evaluation_service.evaluate_routine_impacts.await_args.kwargs

    reminder_my_day = kwargs["my_day"]

    assert reminder_my_day.routines == []


@pytest.mark.asyncio
async def test_approaching_routine_is_sent_for_evaluation():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    routine = build_routine(start_time=time(7, 0))

    my_day_service.get_my_day.return_value = build_my_day(
        routines=[routine],
    )

    evaluation_service.evaluate_official_alerts.return_value = 0
    evaluation_service.evaluate_routine_impacts.return_value = 0
    evaluation_service.evaluate_environmental_conditions.return_value = 0

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    await service.evaluate_candidate(
        candidate=build_candidate(),
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            6,
            40,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    kwargs = evaluation_service.evaluate_routine_impacts.await_args.kwargs

    reminder_my_day = kwargs["my_day"]

    assert reminder_my_day.routines == [routine]

    assert kwargs["reminder_lead_minutes"] == 30


@pytest.mark.asyncio
async def test_started_routine_is_filtered_out():
    weather_service = AsyncMock()
    alert_service = AsyncMock()
    my_day_service = build_my_day_service_mock()
    evaluation_service = AsyncMock()

    weather_service.get_context.return_value = build_context()

    alert_service.get_relevant_alerts.return_value = []

    routine = build_routine(start_time=time(7, 0))

    my_day_service.get_my_day.return_value = build_my_day(
        routines=[routine],
    )

    evaluation_service.evaluate_official_alerts.return_value = 0
    evaluation_service.evaluate_routine_impacts.return_value = 0
    evaluation_service.evaluate_environmental_conditions.return_value = 0

    service = NotificationSweepService(
        weather_context_service=weather_service,
        alert_service=alert_service,
        my_day_service=my_day_service,
        notification_evaluation_service=(evaluation_service),
    )

    await service.evaluate_candidate(
        candidate=build_candidate(),
        target_date=date(2026, 9, 3),
        current_time=datetime(
            2026,
            9,
            3,
            7,
            0,
            tzinfo=UTC,
        ),
        include_daily_summary=False,
    )

    kwargs = evaluation_service.evaluate_routine_impacts.await_args.kwargs

    reminder_my_day = kwargs["my_day"]

    assert reminder_my_day.routines == []
