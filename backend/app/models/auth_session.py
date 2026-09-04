import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.models.base import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    __table_args__ = (
        UniqueConstraint(
            "family_id",
            name="uq_auth_sessions_family_id",
        ),
        Index(
            "ix_auth_sessions_user_revoked",
            "user_id",
            "revoked_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    family_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False,
        default=uuid.uuid4,
    )

    device_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    platform: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship(
        "User",
        back_populates="auth_sessions",
    )
