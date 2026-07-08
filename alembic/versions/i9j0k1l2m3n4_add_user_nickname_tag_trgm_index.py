"""add user nickname tag trgm index

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-07-07 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "i9j0k1l2m3n4"
down_revision: Union[str, None] = "h8i9j0k1l2m3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute(
        """
        CREATE INDEX ix_user_nickname_tag_trgm
        ON "user" USING gin ((nickname || '#' || tag) gin_trgm_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_user_nickname_tag_trgm")
