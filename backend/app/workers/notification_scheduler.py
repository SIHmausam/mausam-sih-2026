import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def should_include_daily_summary(
    now: datetime,
) -> bool:
    hour = now.hour

    return (
        settings.notification_daily_summary_start_hour
        <= hour
        < settings.notification_daily_summary_end_hour
    )


async def run_single_sweep() -> None:
    """
    Execute one notification evaluation sweep.

    The real service wiring will be added next.
    """

    logger.warning("Notification scheduler sweep is not wired yet")


async def run_scheduler() -> None:
    logger.info("Notification scheduler started")

    while True:
        try:
            await run_single_sweep()

        except Exception:
            logger.exception("Notification scheduler sweep failed")

        await asyncio.sleep(settings.notification_scheduler_interval_seconds)


async def main() -> None:
    if not (settings.notification_scheduler_enabled):
        logger.info("Notification scheduler is disabled")

        return

    await run_scheduler()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
