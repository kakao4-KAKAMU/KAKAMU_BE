"""add post feed indexes

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-07-05 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_status_id_desc
          ON post (status, id DESC)
         WHERE status = 'ACTIVE';
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_user_id
          ON post (user_id);
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_post_user_id;")
    op.execute("DROP INDEX IF EXISTS ix_post_status_id_desc;")
