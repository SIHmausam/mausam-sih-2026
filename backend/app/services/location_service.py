import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_location import SavedLocation
from app.repositories.location_repository import LocationRepository
from app.schemas.location import (
    LocationCreateRequest,
    LocationUpdateRequest,
)


class LocationNotFoundError(Exception):
    pass


class LocationService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.repository = LocationRepository(session)

    async def create_location(
        self,
        user_id: uuid.UUID,
        payload: LocationCreateRequest,
    ) -> SavedLocation:
        location = SavedLocation(
            user_id=user_id,
            label=payload.label,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_type=payload.location_type.value,
            is_primary=payload.is_primary,
        )

        try:
            if payload.is_primary:
                await self.repository.clear_primary_locations(user_id=user_id)

            self.repository.add(location)

            await self.session.commit()
            await self.session.refresh(location)

        except Exception:
            await self.session.rollback()
            raise

        return location

    async def list_locations(
        self,
        user_id: uuid.UUID,
    ) -> list[SavedLocation]:
        return await self.repository.list_for_user(user_id)

    async def update_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
        payload: LocationUpdateRequest,
    ) -> SavedLocation:
        location = await self.repository.get_owned_location(
            location_id=location_id,
            user_id=user_id,
        )

        if location is None:
            raise LocationNotFoundError("Location not found")

        fields_set = payload.model_fields_set

        try:
            if "label" in fields_set and payload.label is not None:
                location.label = payload.label

            if "latitude" in fields_set and payload.latitude is not None:
                location.latitude = payload.latitude

            if "longitude" in fields_set and payload.longitude is not None:
                location.longitude = payload.longitude

            if "location_type" in fields_set and payload.location_type is not None:
                location.location_type = payload.location_type.value

            if "is_primary" in fields_set and payload.is_primary is not None:
                if payload.is_primary:
                    await self.repository.clear_primary_locations(
                        user_id=user_id,
                        exclude_location_id=location.id,
                    )

                location.is_primary = payload.is_primary

            await self.session.commit()
            await self.session.refresh(location)

        except Exception:
            await self.session.rollback()
            raise

        return location

    async def delete_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> None:
        location = await self.repository.get_owned_location(
            location_id=location_id,
            user_id=user_id,
        )

        if location is None:
            raise LocationNotFoundError("Location not found")

        try:
            await self.repository.delete(location)
            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise
