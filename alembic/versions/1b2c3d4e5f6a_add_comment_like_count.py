"""add comment like count

Revision ID: 1b2c3d4e5f6a
Revises: 8a9b0c1d2e3f
Create Date: 2026-06-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '1b2c3d4e5f6a'
down_revision: Union[str, None] = '8a9b0c1d2e3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 기존 테이블에 추가되므로 기본값(0)을 설정합니다.
    op.add_column('comment', sa.Column('like_count', sa.Integer(), server_default='0', nullable=False))
    op.create_index(op.f('ix_comment_like_count'), 'comment', ['like_count'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_comment_like_count'), table_name='comment')
    op.drop_column('comment', 'like_count')