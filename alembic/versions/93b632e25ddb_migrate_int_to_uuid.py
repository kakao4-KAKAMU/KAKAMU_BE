"""migrate int to uuid

Revision ID: 93b632e25ddb
Revises: 36b77b456a9a
Create Date: 2026-05-24 00:06:33.806366

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93b632e25ddb'
down_revision: Union[str, None] = '36b77b456a9a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL uuid 확장 모듈 활성화
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # 대상 테이블 분류
    tables_with_user_fk = ['local_auth', 'social_auth', 'persona']
    tables_with_persona_fk = [
        'fav_genre', 'fav_people',
        'post', 'post_mention', 'comment', 'comment_mention',
        'like_log', 'entity_relationship_log'
    ]

    # 1. 임시 UUID 컬럼 추가 (새로운 UUID 자동 생성)
    op.execute('ALTER TABLE "user" ADD COLUMN new_id UUID DEFAULT uuid_generate_v4();')
    op.execute('ALTER TABLE persona ADD COLUMN new_id UUID DEFAULT uuid_generate_v4();')

    for t in tables_with_user_fk:
        op.execute(f'ALTER TABLE {t} ADD COLUMN new_user_id UUID;')
        
    for t in tables_with_persona_fk:
        op.execute(f'ALTER TABLE {t} ADD COLUMN new_persona_id UUID;')
        
    op.execute('ALTER TABLE follow ADD COLUMN new_follower_id UUID;')
    op.execute('ALTER TABLE follow ADD COLUMN new_following_id UUID;')
    op.execute('ALTER TABLE block ADD COLUMN new_blocker_id UUID;')
    op.execute('ALTER TABLE block ADD COLUMN new_blocked_id UUID;')

    # 2. 기존 Integer ID를 기반으로 데이터 매핑(Migration)
    for t in tables_with_user_fk:
        op.execute(f'UPDATE {t} SET new_user_id = u.new_id FROM "user" u WHERE {t}.user_id = u.id;')
        
    for t in tables_with_persona_fk:
        op.execute(f'UPDATE {t} SET new_persona_id = p.new_id FROM persona p WHERE {t}.persona_id = p.id;')
        
    op.execute('UPDATE follow SET new_follower_id = p.new_id FROM persona p WHERE follow.follower_id = p.id;')
    op.execute('UPDATE follow SET new_following_id = p.new_id FROM persona p WHERE follow.following_id = p.id;')
    op.execute('UPDATE block SET new_blocker_id = p.new_id FROM persona p WHERE block.blocker_id = p.id;')
    op.execute('UPDATE block SET new_blocked_id = p.new_id FROM persona p WHERE block.blocked_id = p.id;')

    # 3. 제약 조건 삭제 (외래키 명시적 삭제 후 기본키 삭제)
    for t in tables_with_user_fk:
        op.execute(f'ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {t}_user_id_fkey CASCADE;')
    for t in tables_with_persona_fk:
        op.execute(f'ALTER TABLE {t} DROP CONSTRAINT IF EXISTS {t}_persona_id_fkey CASCADE;')
    op.execute('ALTER TABLE follow DROP CONSTRAINT IF EXISTS follow_follower_id_fkey CASCADE;')
    op.execute('ALTER TABLE follow DROP CONSTRAINT IF EXISTS follow_following_id_fkey CASCADE;')
    op.execute('ALTER TABLE block DROP CONSTRAINT IF EXISTS block_blocker_id_fkey CASCADE;')
    op.execute('ALTER TABLE block DROP CONSTRAINT IF EXISTS block_blocked_id_fkey CASCADE;')

    op.execute('ALTER TABLE "user" DROP CONSTRAINT IF EXISTS user_pkey CASCADE;')
    op.execute('ALTER TABLE persona DROP CONSTRAINT IF EXISTS persona_pkey CASCADE;')
    
    # 복합키(Composite PK) 및 유니크 제약 삭제
    op.execute('ALTER TABLE fav_genre DROP CONSTRAINT IF EXISTS fav_genre_pkey CASCADE;')
    op.execute('ALTER TABLE fav_people DROP CONSTRAINT IF EXISTS fav_people_pkey CASCADE;')
    op.execute('ALTER TABLE follow DROP CONSTRAINT IF EXISTS follow_pkey CASCADE;')
    op.execute('ALTER TABLE block DROP CONSTRAINT IF EXISTS block_pkey CASCADE;')
    op.execute('ALTER TABLE post_mention DROP CONSTRAINT IF EXISTS post_mention_pkey CASCADE;')
    op.execute('ALTER TABLE comment_mention DROP CONSTRAINT IF EXISTS comment_mention_pkey CASCADE;')
    op.execute('ALTER TABLE like_log DROP CONSTRAINT IF EXISTS uq_likelog_persona_target CASCADE;')

    # 4. 기존 Integer 컬럼 삭제
    op.drop_column('user', 'id')
    op.drop_column('persona', 'id')
    for t in tables_with_user_fk:
        op.drop_column(t, 'user_id')
    for t in tables_with_persona_fk:
        op.drop_column(t, 'persona_id')
    op.drop_column('follow', 'follower_id')
    op.drop_column('follow', 'following_id')
    op.drop_column('block', 'blocker_id')
    op.drop_column('block', 'blocked_id')

    # 5. 임시 컬럼 이름을 원래 이름으로 변경
    op.alter_column('user', 'new_id', new_column_name='id', nullable=False)
    op.alter_column('persona', 'new_id', new_column_name='id', nullable=False)
    for t in tables_with_user_fk:
        op.alter_column(t, 'new_user_id', new_column_name='user_id', nullable=False)
    for t in tables_with_persona_fk:
        op.alter_column(t, 'new_persona_id', new_column_name='persona_id', nullable=False)
    op.alter_column('follow', 'new_follower_id', new_column_name='follower_id', nullable=False)
    op.alter_column('follow', 'new_following_id', new_column_name='following_id', nullable=False)
    op.alter_column('block', 'new_blocker_id', new_column_name='blocker_id', nullable=False)
    op.alter_column('block', 'new_blocked_id', new_column_name='blocked_id', nullable=False)

    # 6. 기본키(PK) 및 인덱스 재생성
    op.create_primary_key('user_pkey', 'user', ['id'])
    op.create_primary_key('persona_pkey', 'persona', ['id'])
    op.create_primary_key('fav_genre_pkey', 'fav_genre', ['persona_id', 'genre_id'])
    op.create_primary_key('fav_people_pkey', 'fav_people', ['persona_id', 'people_id'])
    op.create_primary_key('follow_pkey', 'follow', ['follower_id', 'following_id'])
    op.create_primary_key('block_pkey', 'block', ['blocker_id', 'blocked_id'])
    op.create_primary_key('post_mention_pkey', 'post_mention', ['post_id', 'persona_id'])
    op.create_primary_key('comment_mention_pkey', 'comment_mention', ['comment_id', 'persona_id'])

    op.create_unique_constraint('uq_likelog_persona_target', 'like_log', ['persona_id', 'target_type', 'target_id'])

    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    op.create_index(op.f('ix_block_blocker_id'), 'block', ['blocker_id'], unique=False)
    op.create_index(op.f('ix_block_blocked_id'), 'block', ['blocked_id'], unique=False)

    # 7. 외래키(FK) 제약조건 재생성
    for t in tables_with_user_fk:
        op.create_foreign_key(f'{t}_user_id_fkey', t, 'user', ['user_id'], ['id'], ondelete='CASCADE')
        
    for t in tables_with_persona_fk:
        op.create_foreign_key(f'{t}_persona_id_fkey', t, 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
        
    op.create_foreign_key('follow_follower_id_fkey', 'follow', 'persona', ['follower_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('follow_following_id_fkey', 'follow', 'persona', ['following_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('block_blocker_id_fkey', 'block', 'persona', ['blocker_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('block_blocked_id_fkey', 'block', 'persona', ['blocked_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # UUID에서 Integer로 다운그레이드 하는 것은 참조 무결성 충돌 및 ID 복원 문제로 인해 
    # 일반적으로 스크립트로 처리하지 않으므로 지원 불가 예외를 던집니다.
    raise NotImplementedError("데이터 무결성 문제로 인해 UUID에서 Integer로의 다운그레이드는 지원하지 않습니다.")