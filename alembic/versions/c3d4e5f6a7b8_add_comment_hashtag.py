"""add comment hashtag

Revision ID: c3d4e5f6a7b8
Revises: 1b2c3d4e5f6a
Create Date: 2026-06-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '1b2c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('comment_hashtag',
    sa.Column('comment_id', sa.Integer(), nullable=False),
    sa.Column('hashtag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['comment_id'], ['comment.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['hashtag_id'], ['hashtag.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('comment_id', 'hashtag_id')
    )

def downgrade() -> None:
    op.drop_table('comment_hashtag')