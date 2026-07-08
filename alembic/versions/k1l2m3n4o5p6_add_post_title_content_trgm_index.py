"""add post title content composite trgm index

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-07-08 21:40:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "k1l2m3n4o5p6"
down_revision: Union[str, None] = "j0k1l2m3n4o5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
    op.execute(
        """
        CREATE INDEX ix_post_title_content_trgm
          ON post USING gin (title gin_trgm_ops, content gin_trgm_ops)
         WHERE status = 'ACTIVE';
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_post_title_trgm;")
    op.execute("DROP INDEX IF EXISTS ix_post_content_trgm;")


def downgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_title_trgm
          ON post USING gin (title gin_trgm_ops);
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_content_trgm
          ON post USING gin (content gin_trgm_ops);
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_post_title_content_trgm;")
