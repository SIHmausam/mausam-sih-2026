import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.saved_location import SavedLocation


class LocationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
        self,
        location_id: uuid.UUID,
    ) -> SavedLocation | None:
        result = await self.session.execute(
            select(SavedLocation).where(SavedLocation.id == location_id)
        )

        return result.scalar_one_or_none()

    async def get_owned_location(
        self,
        location_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> SavedLocation | None:
        result = await self.session.execute(
            select(SavedLocation).where(
                SavedLocation.id == location_id,
                SavedLocation.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[SavedLocation]:
        result = await self.session.execute(
            select(SavedLocation)
            .where(SavedLocation.user_id == user_id)
            .order_by(
                SavedLocation.is_primary.desc(),
                SavedLocation.created_at.asc(),
            )
        )

        return list(result.scalars().all())

    def add(
        self,
        location: SavedLocation,
    ) -> None:
        self.session.add(location)

    async def clear_primary_locations(
        self,
        user_id: uuid.UUID,
        exclude_location_id: uuid.UUID | None = None,
    ) -> None:
        statement = (
            update(SavedLocation)
            .where(SavedLocation.user_id == user_id)
            .values(is_primary=False)
        )

        if exclude_location_id is not None:
            statement = statement.where(SavedLocation.id != exclude_location_id)

        await self.session.execute(statement)

    async def delete(
        self,
        location: SavedLocation,
    ) -> None:
        await self.session.delete(location)
