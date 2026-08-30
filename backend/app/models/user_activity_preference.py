import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserActivityPreference(Base):
    __tablename__ = "user_activity_preferences"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "activity_context",
            name="uq_user_activity_context",
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

    activity_context: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="activity_preferences",
    )