"""add city to saved locations

Revision ID: 8b7c1e4a2d90
Revises: 53e552546a2e

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8b7c1e4a2d90"
down_revision: str | Sequence[str] | None = "53e552546a2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "saved_locations",
        sa.Column(
            "city",
            sa.String(length=100),
            nullable=False,
            server_default="unknown",
        ),
    )

    # The temporary default keeps this migration safe
    # if local databases already contain saved locations.
    # New API requests must always supply a real city.
    op.alter_column(
        "saved_locations",
        "city",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "saved_locations",
        "city",
    )
