import logging
from dataclasses import dataclass
from datetime import date

from app.repositories.notification_candidate_repository import (
    NotificationCandidate,
)
from app.services.alert_service import AlertService
from app.services.my_day_service import MyDayService
from app.services.notification_evaluation_service import (
    NotificationEvaluationService,
)
from app.services.weather_context_service import (
    WeatherContextService,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationSweepResult:
    processed_users: int
    failed_users: int
    notifications_created: int


class NotificationSweepService:
    def __init__(
        self,
        *,
        weather_context_service: WeatherContextService,
        alert_service: AlertService,
        my_day_service: MyDayService,
        notification_evaluation_service: (NotificationEvaluationService),
    ):
        self.weather_context_service = weather_context_service

        self.alert_service = alert_service

        self.my_day_service = my_day_service

        self.notification_evaluation_service = notification_evaluation_service

    async def evaluate_candidate(
        self,
        *,
        candidate: NotificationCandidate,
        target_date: date,
        include_daily_summary: bool,
    ) -> int:
        context = await self.weather_context_service.get_context(
            latitude=candidate.latitude,
            longitude=candidate.longitude,
        )

        alerts = await self.alert_service.get_relevant_alerts(
            latitude=candidate.latitude,
            longitude=candidate.longitude,
            city=candidate.city,
        )

        my_day = await self.my_day_service.get_my_day(
            user_id=candidate.user_id,
            target_date=target_date,
        )

        created_count = 0

        created_count += (
            await self.notification_evaluation_service.evaluate_official_alerts(
                user_id=candidate.user_id,
                location_id=(candidate.location_id),
                alerts=alerts,
            )
        )

        created_count += (
            await self.notification_evaluation_service.evaluate_routine_impacts(
                user_id=candidate.user_id,
                my_day=my_day,
            )
        )

        created_count += await self.notification_evaluation_service.evaluate_environmental_conditions(
            user_id=candidate.user_id,
            location_id=(candidate.location_id),
            context=context,
            target_date=target_date,
        )

        if include_daily_summary:
            created_count += (
                await self.notification_evaluation_service.evaluate_daily_summary(
                    user_id=(candidate.user_id),
                    location_id=(candidate.location_id),
                    context=context,
                    my_day=my_day,
                    target_date=target_date,
                )
            )

        return created_count

    async def run_sweep(
        self,
        *,
        candidates: list[NotificationCandidate],
        target_date: date,
        include_daily_summary: bool,
    ) -> NotificationSweepResult:
        processed_users = 0
        failed_users = 0
        notifications_created = 0

        for candidate in candidates:
            try:
                created = await self.evaluate_candidate(
                    candidate=candidate,
                    target_date=target_date,
                    include_daily_summary=(include_daily_summary),
                )

                processed_users += 1
                notifications_created += created

            except Exception:
                failed_users += 1

                logger.exception(
                    "Notification evaluation failed for user %s",
                    candidate.user_id,
                )

        return NotificationSweepResult(
            processed_users=processed_users,
            failed_users=failed_users,
            notifications_created=(notifications_created),
        )
