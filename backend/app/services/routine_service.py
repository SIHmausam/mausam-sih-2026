import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_routine import UserRoutine
from app.repositories.location_repository import (
    LocationRepository,
)
from app.repositories.routine_repository import (
    RoutineRepository,
)
from app.schemas.routine import (
    RoutineCreateRequest,
    RoutineUpdateRequest,
)


class RoutineNotFoundError(Exception):
    pass


class RoutineLocationNotFoundError(Exception):
    pass


class RoutineService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

        self.repository = RoutineRepository(session)

        self.location_repository = LocationRepository(session)

    async def _validate_location(
        self,
        user_id: uuid.UUID,
        location_id: uuid.UUID,
    ) -> None:
        location = await self.location_repository.get_owned_location(
            location_id=location_id,
            user_id=user_id,
        )

        if location is None:
            raise RoutineLocationNotFoundError("Saved location not found")

    async def create_routine(
        self,
        user_id: uuid.UUID,
        payload: RoutineCreateRequest,
    ) -> UserRoutine:
        if payload.saved_location_id is not None:
            await self._validate_location(
                user_id=user_id,
                location_id=payload.saved_location_id,
            )

        routine = UserRoutine(
            user_id=user_id,
            name=payload.name.strip(),
            activity_context=(payload.activity_context.value),
            saved_location_id=(payload.saved_location_id),
            days_of_week=[day.value for day in payload.days_of_week],
            start_time=payload.start_time,
            duration_minutes=(payload.duration_minutes),
            is_enabled=payload.is_enabled,
        )

        try:
            self.repository.add(routine)

            await self.session.commit()
            await self.session.refresh(routine)

        except Exception:
            await self.session.rollback()
            raise

        return routine

    async def list_routines(
        self,
        user_id: uuid.UUID,
    ) -> list[UserRoutine]:
        return await self.repository.list_for_user(user_id)

    async def update_routine(
        self,
        user_id: uuid.UUID,
        routine_id: uuid.UUID,
        payload: RoutineUpdateRequest,
    ) -> UserRoutine:
        routine = await self.repository.get_owned_routine(
            routine_id=routine_id,
            user_id=user_id,
        )

        if routine is None:
            raise RoutineNotFoundError("Routine not found")

        fields = payload.model_fields_set

        if "saved_location_id" in fields and payload.saved_location_id is not None:
            await self._validate_location(
                user_id=user_id,
                location_id=payload.saved_location_id,
            )

        try:
            if "name" in fields and payload.name is not None:
                routine.name = payload.name.strip()

            if "activity_context" in fields and payload.activity_context is not None:
                routine.activity_context = payload.activity_context.value

            if "saved_location_id" in fields:
                routine.saved_location_id = payload.saved_location_id

            if "days_of_week" in fields and payload.days_of_week is not None:
                routine.days_of_week = [day.value for day in payload.days_of_week]

            if "start_time" in fields and payload.start_time is not None:
                routine.start_time = payload.start_time

            if "duration_minutes" in fields and payload.duration_minutes is not None:
                routine.duration_minutes = payload.duration_minutes

            if "is_enabled" in fields and payload.is_enabled is not None:
                routine.is_enabled = payload.is_enabled

            await self.session.commit()

            await self.session.refresh(routine)

        except Exception:
            await self.session.rollback()
            raise

        return routine

    async def delete_routine(
        self,
        user_id: uuid.UUID,
        routine_id: uuid.UUID,
    ) -> None:
        routine = await self.repository.get_owned_routine(
            routine_id=routine_id,
            user_id=user_id,
        )

        if routine is None:
            raise RoutineNotFoundError("Routine not found")

        try:
            await self.repository.delete(routine)

            await self.session.commit()

        except Exception:
            await self.session.rollback()
            raise
