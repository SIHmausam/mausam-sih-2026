import uuid
from datetime import datetime

from sqlalchemy import (
    desc,
    select,
)
from sqlalchemy.ext.asyncio import (
    AsyncSession,
)

from app.models.user_interaction import (
    UserInteraction,
)


class InteractionRepository:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        card_type: str,
        action: str,
        position: int,
        session_id: str,
        occurred_at: datetime,
    ) -> UserInteraction:
        interaction = UserInteraction(
            user_id=user_id,
            card_type=card_type,
            action=action,
            position=position,
            session_id=session_id,
            occurred_at=occurred_at,
        )

        self.session.add(interaction)

        await self.session.flush()

        return interaction

    async def list_recent_for_user(
        self,
        *,
        user_id: uuid.UUID,
        limit: int = 100,
    ) -> list[UserInteraction]:
        result = await self.session.execute(
            select(UserInteraction)
            .where(UserInteraction.user_id == user_id)
            .order_by(desc(UserInteraction.occurred_at))
            .limit(limit)
        )

        return list(result.scalars().all())
