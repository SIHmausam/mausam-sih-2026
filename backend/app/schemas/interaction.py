import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.enums import (
    CardType,
    InteractionAction,
)


class InteractionCreateRequest(BaseModel):
    card_type: CardType

    action: InteractionAction

    # Standardize positions as 1-based:
    # first visible card = 1
    # last card = 8
    position: int = Field(
        ge=1,
        le=8,
    )

    session_id: str = Field(
        min_length=1,
        max_length=100,
    )


class InteractionResponse(BaseModel):
    id: uuid.UUID

    card_type: CardType

    action: InteractionAction

    position: int

    session_id: str

    occurred_at: datetime

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
