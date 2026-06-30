"""add save_log table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-30 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'save_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('persona_id', sa.UUID(), nullable=True),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('movie_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['persona_id'], ['persona.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_savelog_target', 'save_log', ['target_type', 'target_id'], unique=False)
    op.create_index('ix_savelog_movie', 'save_log', ['target_type', 'movie_id'], unique=False)
    op.create_index(
        'uq_savelog_user_post_comment',
        'save_log',
        ['user_id', 'target_type', 'target_id'],
        unique=True,
        postgresql_where=sa.text('target_id IS NOT NULL'),
    )
    op.create_index(
        'uq_savelog_user_movie',
        'save_log',
        ['user_id', 'target_type', 'movie_id'],
        unique=True,
        postgresql_where=sa.text('movie_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_savelog_user_movie', table_name='save_log')
    op.drop_index('uq_savelog_user_post_comment', table_name='save_log')
    op.drop_index('ix_savelog_movie', table_name='save_log')
    op.drop_index('ix_savelog_target', table_name='save_log')
    op.drop_table('save_log')
