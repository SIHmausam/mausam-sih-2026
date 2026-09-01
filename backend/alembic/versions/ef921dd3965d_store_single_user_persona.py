"""store single user persona

Revision ID: ef921dd3965d
Revises: c8899ccdabb2
Create Date: 2026-09-01 22:23:57.546225

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ef921dd3965d"
down_revision: str | Sequence[str] | None = "c8899ccdabb2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "user_preferences",
        sa.Column(
            "persona",
            sa.String(length=50),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE user_preferences AS preferences
        SET persona = single_persona.persona
        FROM (
            SELECT
                user_id,
                MIN(persona) AS persona
            FROM user_personas
            GROUP BY user_id
            HAVING COUNT(*) = 1
        ) AS single_persona
        WHERE
            preferences.user_id = single_persona.user_id
        """
    )

    op.execute(
        """
        UPDATE user_preferences
        SET onboarding_completed = FALSE
        WHERE persona IS NULL
        """
    )

    op.drop_index(
        op.f("ix_user_personas_user_id"),
        table_name="user_personas",
    )

    op.drop_table("user_personas")


def downgrade() -> None:
    """Downgrade schema."""

    op.create_table(
        "user_personas",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
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
            name=op.f("user_personas_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f("user_personas_pkey"),
        ),
        sa.UniqueConstraint(
            "user_id",
            "persona",
            name=op.f("uq_user_persona"),
        ),
    )

    op.create_index(
        op.f("ix_user_personas_user_id"),
        "user_personas",
        ["user_id"],
        unique=False,
    )

    connection = op.get_bind()

    result = connection.execute(
        sa.text(
            """
            SELECT user_id, persona
            FROM user_preferences
            WHERE persona IS NOT NULL
            """
        )
    )

    user_personas_table = sa.table(
        "user_personas",
        sa.column(
            "id",
            sa.UUID(),
        ),
        sa.column(
            "user_id",
            sa.UUID(),
        ),
        sa.column(
            "persona",
            sa.String(length=50),
        ),
    )

    rows = [
        {
            "id": uuid.uuid4(),
            "user_id": row.user_id,
            "persona": row.persona,
        }
        for row in result
    ]

    if rows:
        op.bulk_insert(
            user_personas_table,
            rows,
        )

    op.drop_column(
        "user_preferences",
        "persona",
    )
