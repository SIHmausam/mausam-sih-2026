"""add user personas

Revision ID: 10f6ae6367d0
Revises: f49d5a986785
Create Date: 2026-09-15 11:30:56.292267
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "10f6ae6367d0"
down_revision: str | Sequence[str] | None = "f49d5a986785"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "user_personas",
        sa.Column(
            "user_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "persona",
            sa.String(length=50),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "user_id",
            "persona",
        ),
    )

    # Backfill the existing single persona selection
    # into the new multi-persona table.
    op.execute(
        """
        INSERT INTO user_personas (
            user_id,
            persona
        )
        SELECT
            user_id,
            persona
        FROM user_preferences
        WHERE persona IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table("user_personas")