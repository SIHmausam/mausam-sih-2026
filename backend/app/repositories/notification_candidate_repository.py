import uuid
from dataclasses import dataclass

from sqlalchemy import (
    or_,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_location import SavedLocation
from app.models.user_preference import UserPreference


@dataclass(frozen=True)
class NotificationCandidate:
    user_id: uuid.UUID

    location_id: uuid.UUID
    city: str

    latitude: float
    longitude: float


class NotificationCandidateRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def list_candidates(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NotificationCandidate]:
        statement = (
            select(
                UserPreference.user_id,
                SavedLocation.id,
                SavedLocation.city,
                SavedLocation.latitude,
                SavedLocation.longitude,
            )
            .join(
                SavedLocation,
                SavedLocation.user_id == UserPreference.user_id,
            )
            .where(
                UserPreference.onboarding_completed.is_(True),
                SavedLocation.is_primary.is_(True),
                or_(
                    UserPreference.official_alerts_enabled.is_(True),
                    UserPreference.routine_alerts_enabled.is_(True),
                    UserPreference.rain_alerts_enabled.is_(True),
                    UserPreference.aqi_alerts_enabled.is_(True),
                    UserPreference.daily_summary_enabled.is_(True),
                ),
            )
            .order_by(UserPreference.user_id)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(statement)

        return [
            NotificationCandidate(
                user_id=row.user_id,
                location_id=row.id,
                city=row.city,
                latitude=row.latitude,
                longitude=row.longitude,
            )
            for row in result.all()
        ]
