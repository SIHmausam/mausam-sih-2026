import asyncio
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
)
from app.core.redis import get_redis
from app.dependencies.providers import (
    get_air_quality_provider,
    get_alert_provider,
    get_push_provider,
    get_weather_provider,
)
from app.repositories.notification_candidate_repository import (
    NotificationCandidateRepository,
)
from app.services.air_quality_service import (
    AirQualityService,
)
from app.services.alert_service import (
    AlertService,
)
from app.services.my_day_service import (
    MyDayService,
)
from app.services.notification_evaluation_service import (
    NotificationEvaluationService,
)
from app.services.notification_sweep_service import (
    NotificationSweepService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)
from app.services.weather_service import (
    WeatherService,
)

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
    Execute one complete proactive
    notification evaluation sweep.

    This runs independently of FastAPI,
    so users can receive notifications
    without opening the application.
    """

    started_at = datetime.now(IST)

    target_date = started_at.date()

    include_daily_summary = should_include_daily_summary(started_at)

    logger.info(
        "Starting notification sweep for %s; daily_summary=%s",
        target_date,
        include_daily_summary,
    )

    redis = await get_redis()

    weather_provider = get_weather_provider()

    air_quality_provider = get_air_quality_provider()

    alert_provider = get_alert_provider()

    push_provider = get_push_provider()

    processed_users = 0
    failed_users = 0
    notifications_created = 0

    offset = 0

    batch_size = settings.notification_scheduler_batch_size

    async with AsyncSessionLocal() as session:
        weather_service = WeatherService(
            provider=weather_provider,
            redis=redis,
        )

        air_quality_service = AirQualityService(
            provider=(air_quality_provider),
            redis=redis,
        )

        weather_context_service = WeatherContextService(
            weather_service=(weather_service),
            air_quality_service=(air_quality_service),
        )

        alert_service = AlertService(
            provider=alert_provider,
            redis=redis,
        )

        my_day_service = MyDayService(
            session=session,
            weather_context_service=(weather_context_service),
            alert_service=alert_service,
        )

        notification_evaluation_service = NotificationEvaluationService(
            session=session,
            push_provider=(push_provider),
        )

        sweep_service = NotificationSweepService(
            session=session,
            weather_context_service=(weather_context_service),
            alert_service=(alert_service),
            my_day_service=(my_day_service),
            notification_evaluation_service=(notification_evaluation_service),
        )

        candidate_repository = NotificationCandidateRepository(session)

        while True:
            candidates = await candidate_repository.list_candidates(
                limit=batch_size,
                offset=offset,
            )

            if not candidates:
                break

            result = await sweep_service.run_sweep(
                candidates=candidates,
                target_date=(target_date),
                include_daily_summary=(include_daily_summary),
            )

            processed_users += result.processed_users

            failed_users += result.failed_users

            notifications_created += result.notifications_created

            if len(candidates) < batch_size:
                break

            offset += batch_size

    finished_at = datetime.now(IST)

    duration_seconds = (finished_at - started_at).total_seconds()

    logger.info(
        "Notification sweep complete: processed=%s failed=%s created=%s duration=%.2fs",
        processed_users,
        failed_users,
        notifications_created,
        duration_seconds,
    )


async def run_scheduler() -> None:
    logger.info(
        "Notification scheduler started with interval=%ss",
        settings.notification_scheduler_interval_seconds,
    )

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
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s %(levelname)s %(name)s - %(message)s"),
    )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Notification scheduler stopped")
