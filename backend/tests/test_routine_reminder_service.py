from datetime import (
    UTC,
    date,
    datetime,
    time,
)
from types import SimpleNamespace

import pytest

from app.services.routine_reminder_service import (
    RoutineReminderService,
)


def make_my_day(
    *,
    routine_time: time = time(7, 0),
):
    routine = SimpleNamespace(
        routine_id="routine-1",
        start_time=routine_time,
    )

    return SimpleNamespace(
        date=date(2026, 9, 6),
        routines=[routine],
    )


def test_routine_not_approaching_before_window():
    service = RoutineReminderService(reminder_lead_minutes=30)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        6,
        29,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert result == []


def test_routine_approaching_at_window_start():
    service = RoutineReminderService(reminder_lead_minutes=30)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        6,
        30,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert len(result) == 1


def test_routine_approaching_inside_window():
    service = RoutineReminderService(reminder_lead_minutes=30)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        6,
        45,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert len(result) == 1


def test_routine_not_approaching_at_start_time():
    service = RoutineReminderService(reminder_lead_minutes=30)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        7,
        0,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert result == []


def test_routine_not_approaching_after_start():
    service = RoutineReminderService(reminder_lead_minutes=30)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        7,
        10,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert result == []


def test_custom_lead_time():
    service = RoutineReminderService(reminder_lead_minutes=60)

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        6,
        0,
        tzinfo=UTC,
    )

    result = service.get_approaching_routines(
        my_day=my_day,
        now=now,
    )

    assert len(result) == 1


def test_requires_timezone_aware_now():
    service = RoutineReminderService()

    my_day = make_my_day()

    now = datetime(
        2026,
        9,
        6,
        6,
        30,
        tzinfo=UTC,
    ).replace(tzinfo=None)

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        service.get_approaching_routines(
            my_day=my_day,
            now=now,
        )


def test_invalid_lead_time():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        RoutineReminderService(reminder_lead_minutes=0)
