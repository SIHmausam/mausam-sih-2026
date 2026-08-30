import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserPersona(Base):
    __tablename__ = "user_personas"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "persona",
            name="uq_user_persona",
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

    persona: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="personas",
    )