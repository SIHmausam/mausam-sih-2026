import uuid

from sqlalchemy import (
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base


class UserPersona(Base):
    __tablename__ = "user_personas"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    persona: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
    )

    user = relationship(
        "User",
        back_populates="personas",
    )