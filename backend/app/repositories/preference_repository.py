import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_activity_preference import UserActivityPreference
from app.models.user_persona import UserPersona
from app.models.user_preference import UserPreference
from app.models.user_weather_interest import UserWeatherInterest


class PreferenceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_preference(
        self,
        user_id: uuid.UUID,
    ) -> UserPreference | None:
        result = await self.session.execute(
            select(UserPreference).where(
                UserPreference.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_personas(
        self,
        user_id: uuid.UUID,
    ) -> list[UserPersona]:
        result = await self.session.execute(
            select(UserPersona).where(
                UserPersona.user_id == user_id
            )
        )
        return list(result.scalars().all())

    async def get_interests(
        self,
        user_id: uuid.UUID,
    ) -> list[UserWeatherInterest]:
        result = await self.session.execute(
            select(UserWeatherInterest).where(
                UserWeatherInterest.user_id == user_id
            )
        )
        return list(result.scalars().all())

    async def get_activity_preferences(
        self,
        user_id: uuid.UUID,
    ) -> list[UserActivityPreference]:
        result = await self.session.execute(
            select(UserActivityPreference).where(
                UserActivityPreference.user_id == user_id
            )
        )
        return list(result.scalars().all())

    def add_preference(
        self,
        preference: UserPreference,
    ) -> None:
        self.session.add(preference)

    def add_personas(
        self,
        personas: list[UserPersona],
    ) -> None:
        self.session.add_all(personas)

    def add_interests(
        self,
        interests: list[UserWeatherInterest],
    ) -> None:
        self.session.add_all(interests)

    def add_activity_preferences(
        self,
        activities: list[UserActivityPreference],
    ) -> None:
        self.session.add_all(activities)

    async def replace_personas(
        self,
        user_id: uuid.UUID,
        personas: list[UserPersona],
    ) -> None:
        await self.session.execute(
            delete(UserPersona).where(
                UserPersona.user_id == user_id
            )
        )
        self.session.add_all(personas)

    async def replace_interests(
        self,
        user_id: uuid.UUID,
        interests: list[UserWeatherInterest],
    ) -> None:
        await self.session.execute(
            delete(UserWeatherInterest).where(
                UserWeatherInterest.user_id == user_id
            )
        )
        self.session.add_all(interests)

    async def replace_activity_preferences(
        self,
        user_id: uuid.UUID,
        activities: list[UserActivityPreference],
    ) -> None:
        await self.session.execute(
            delete(UserActivityPreference).where(
                UserActivityPreference.user_id == user_id
            )
        )
        self.session.add_all(activities)