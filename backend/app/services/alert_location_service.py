import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.location_repository import (
    LocationRepository,
)
from app.schemas.alert import (
    SavedLocationAlertResponse,
)
from app.services.alert_service import AlertService


class AlertLocationNotFoundError(Exception):
    pass


class AlertLocationService:
    def __init__(
        self,
        session: AsyncSession,
        alert_service: AlertService,
    ):
        self.location_repository = LocationRepository(session)

        self.alert_service = alert_service

    async def get_for_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> SavedLocationAlertResponse:
        location = await self.location_repository.get_owned_location(
            location_id=location_id,
            user_id=user_id,
        )

        if location is None:
            raise AlertLocationNotFoundError("Saved location not found")

        alerts = await self.alert_service.get_relevant_alerts(
            latitude=location.latitude,
            longitude=location.longitude,
            city=location.city,
        )

        return SavedLocationAlertResponse(
            location_id=location.id,
            label=location.label,
            city=location.city,
            latitude=location.latitude,
            longitude=location.longitude,
            alerts=alerts,
        )

    async def get_for_primary_location(
        self,
        user_id: uuid.UUID,
    ) -> SavedLocationAlertResponse:
        location = await self.location_repository.get_primary_for_user(user_id=user_id)

        if location is None:
            raise AlertLocationNotFoundError("Primary saved location not found")

        alerts = await self.alert_service.get_relevant_alerts(
            latitude=location.latitude,
            longitude=location.longitude,
            city=location.city,
        )

        return SavedLocationAlertResponse(
            location_id=location.id,
            label=location.label,
            city=location.city,
            latitude=location.latitude,
            longitude=location.longitude,
            alerts=alerts,
        )
