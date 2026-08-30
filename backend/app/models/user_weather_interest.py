import uuid

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserWeatherInterest(Base):
    __tablename__ = "user_weather_interests"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "interest",
            name="uq_user_weather_interest",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    interest: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    internal_weight: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    user = relationship(
        "User",
        back_populates="weather_interests",
    )
