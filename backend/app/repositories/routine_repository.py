import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_routine import UserRoutine


class RoutineRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    def add(
        self,
        routine: UserRoutine,
    ) -> None:
        self.session.add(routine)

    async def get_owned_routine(
        self,
        routine_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> UserRoutine | None:
        result = await self.session.execute(
            select(UserRoutine).where(
                UserRoutine.id == routine_id,
                UserRoutine.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[UserRoutine]:
        result = await self.session.execute(
            select(UserRoutine)
            .where(UserRoutine.user_id == user_id)
            .order_by(UserRoutine.start_time.asc())
        )

        return list(result.scalars().all())

    async def delete(
        self,
        routine: UserRoutine,
    ) -> None:
        await self.session.delete(routine)

    async def list_enabled_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[UserRoutine]:
        result = await self.session.execute(
            select(UserRoutine)
            .where(
                UserRoutine.user_id == user_id,
                UserRoutine.is_enabled.is_(True),
            )
            .order_by(UserRoutine.start_time.asc())
        )

        return list(result.scalars().all())
