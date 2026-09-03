from datetime import datetime
from zoneinfo import ZoneInfo

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
