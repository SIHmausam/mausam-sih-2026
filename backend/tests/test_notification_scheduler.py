from datetime import datetime
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

from app.workers.notification_scheduler import (
    should_include_daily_summary,
)

IST = ZoneInfo("Asia/Kolkata")


def test_daily_summary_inside_window(
    monkeypatch,
):
    from app.workers import (
        notification_scheduler,
    )

    monkeypatch.setattr(
        notification_scheduler.settings,
        "notification_daily_summary_start_hour",
        6,
    )

    monkeypatch.setattr(
        notification_scheduler.settings,
        "notification_daily_summary_end_hour",
        10,
    )

    current = datetime(
        2026,
        9,
        3,
        8,
        0,
        tzinfo=IST,
    )

    assert should_include_daily_summary(current) is True


def test_daily_summary_outside_window(
    monkeypatch,
):
    from app.workers import (
        notification_scheduler,
    )

    monkeypatch.setattr(
        notification_scheduler.settings,
        "notification_daily_summary_start_hour",
        6,
    )

    monkeypatch.setattr(
        notification_scheduler.settings,
        "notification_daily_summary_end_hour",
        10,
    )

    current = datetime(
        2026,
        9,
        3,
        14,
        0,
        tzinfo=IST,
    )

    assert should_include_daily_summary(current) is False


@pytest.mark.asyncio
async def test_disabled_scheduler_does_not_run_sweep(
    monkeypatch,
):
    from app.workers import (
        notification_scheduler,
    )

    monkeypatch.setattr(
        notification_scheduler.settings,
        "notification_scheduler_enabled",
        False,
    )

    run_sweep = AsyncMock()

    monkeypatch.setattr(
        notification_scheduler,
        "run_scheduler",
        run_sweep,
    )

    await notification_scheduler.main()

    run_sweep.assert_not_awaited()
