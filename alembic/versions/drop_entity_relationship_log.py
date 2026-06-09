"""drop entity_relationship_log table

Revision ID: drop_entity_relationship_log
Revises: 6e54293d8157
Create Date: 2026-06-09 16:40:05.608895

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'drop_entity_relationship_log'
down_revision: Union[str, None] ='6e54293d8157'  # 주의: 이 값을 이전 리비전 ID로 채워야 작동합니다!
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 테이블에 걸려있던 인덱스 먼저 삭제
    op.drop_index('ix_entity_log_target', table_name='entity_relationship_log')
    # 테이블 영구 삭제
    op.drop_table('entity_relationship_log')

def downgrade() -> None:
    # 롤백 시 테이블 복구 로직
    op.create_table(
        'entity_relationship_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('persona_id', postgresql.UUID(as_uuid=True), autoincrement=False, nullable=False),
        sa.Column('relation_type', sa.String(length=30), autoincrement=False, nullable=True),
        sa.Column('target_type', sa.String(length=30), autoincrement=False, nullable=True),
        sa.Column('target_id', sa.Integer(), autoincrement=False, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(['persona_id'], ['persona.id'], name='entity_relationship_log_persona_id_fkey', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='entity_relationship_log_pkey')
    )
    op.create_index('ix_entity_log_target', 'entity_relationship_log', ['target_type', 'target_id'], unique=False)