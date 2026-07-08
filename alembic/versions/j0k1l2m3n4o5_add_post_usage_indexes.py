"""add post usage-based indexes

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-07-07 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "j0k1l2m3n4o5"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 프로필 게시물 목록·게시물 수 집계 (user_id + id DESC, ACTIVE만)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_user_active_id_desc
          ON post (user_id, id DESC)
         WHERE status = 'ACTIVE';
        """
    )
    # for-you fallback / 인기순 검색 (like_count DESC, id DESC, ACTIVE만)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_active_like_count_id_desc
          ON post (like_count DESC, id DESC)
         WHERE status = 'ACTIVE';
        """
    )
    # 복합 인덱스로 대체되므로 단일 컬럼 인덱스 제거
    op.execute("DROP INDEX IF EXISTS ix_post_like_count;")


def downgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_post_like_count
          ON post (like_count);
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_post_active_like_count_id_desc;")
    op.execute("DROP INDEX IF EXISTS ix_post_user_active_id_desc;")
