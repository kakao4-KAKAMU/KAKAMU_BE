"""fix database 260604

Revision ID: 97d3a93995e1
Revises: 694987df1e6a
Create Date: 2026-06-05 09:20:36.193150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97d3a93995e1'
down_revision: Union[str, None] = '694987df1e6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add user columns
    op.add_column('user', sa.Column('status', sa.String(length=20), nullable=True))
    op.add_column('user', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # 2. Add user_id column as nullable=True first
    op.add_column('comment', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('comment_mention', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('like_log', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('post', sa.Column('user_id', sa.UUID(), nullable=True))
    op.add_column('post_mention', sa.Column('user_id', sa.UUID(), nullable=True))

    # 3. Migrate data: populate user_id using persona table
    op.execute("""
        UPDATE post SET user_id = persona.user_id FROM persona WHERE post.persona_id = persona.id;
        UPDATE comment SET user_id = persona.user_id FROM persona WHERE comment.persona_id = persona.id;
        UPDATE comment_mention SET user_id = persona.user_id FROM persona WHERE comment_mention.persona_id = persona.id;
        UPDATE like_log SET user_id = persona.user_id FROM persona WHERE like_log.persona_id = persona.id;
        UPDATE post_mention SET user_id = persona.user_id FROM persona WHERE post_mention.persona_id = persona.id;
    """)

    # 3.1 고아 데이터(매칭되는 persona가 없어서 user_id가 NULL인 경우) 삭제
    op.execute("DELETE FROM post WHERE user_id IS NULL;")
    op.execute("DELETE FROM comment WHERE user_id IS NULL;")
    op.execute("DELETE FROM comment_mention WHERE user_id IS NULL;")
    op.execute("DELETE FROM like_log WHERE user_id IS NULL;")
    op.execute("DELETE FROM post_mention WHERE user_id IS NULL;")

    # Alter column to nullable=False
    op.alter_column('comment', 'user_id', nullable=False)
    op.alter_column('comment_mention', 'user_id', nullable=False)
    op.alter_column('like_log', 'user_id', nullable=False)
    op.alter_column('post', 'user_id', nullable=False)
    op.alter_column('post_mention', 'user_id', nullable=False)

    # 4. Migrate follow and block tables
    op.drop_constraint('block_blocker_id_fkey', 'block', type_='foreignkey')
    op.drop_constraint('block_blocked_id_fkey', 'block', type_='foreignkey')
    op.drop_constraint('follow_following_id_fkey', 'follow', type_='foreignkey')
    op.drop_constraint('follow_follower_id_fkey', 'follow', type_='foreignkey')

    # Drop primary keys temporarily to avoid duplicates during update
    op.execute("ALTER TABLE block DROP CONSTRAINT block_pkey")
    op.execute("ALTER TABLE follow DROP CONSTRAINT follow_pkey")

    # Update UUIDs from persona_id to user_id
    op.execute("""
        UPDATE block SET 
            blocker_id = p1.user_id, 
            blocked_id = p2.user_id 
        FROM persona p1, persona p2 
        WHERE block.blocker_id = p1.id AND block.blocked_id = p2.id;
    """)
    op.execute("""
        UPDATE follow SET 
            follower_id = p1.user_id, 
            following_id = p2.user_id 
        FROM persona p1, persona p2 
        WHERE follow.follower_id = p1.id AND follow.following_id = p2.id;
    """)

    # Remove duplicates (keep the earliest one)
    op.execute("""
        DELETE FROM block a USING block b
        WHERE a.blocker_id = b.blocker_id 
          AND a.blocked_id = b.blocked_id 
          AND a.ctid > b.ctid;
    """)
    op.execute("""
        DELETE FROM follow a USING follow b
        WHERE a.follower_id = b.follower_id 
          AND a.following_id = b.following_id 
          AND a.ctid > b.ctid;
    """)

    # Delete self-follows or self-blocks
    op.execute("DELETE FROM block WHERE blocker_id = blocked_id;")
    op.execute("DELETE FROM follow WHERE follower_id = following_id;")

    # Re-add primary keys
    op.execute("ALTER TABLE block ADD PRIMARY KEY (blocker_id, blocked_id)")
    op.execute("ALTER TABLE follow ADD PRIMARY KEY (follower_id, following_id)")

    # Re-add foreign keys to user table
    op.create_foreign_key('block_blocker_id_fkey', 'block', 'user', ['blocker_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('block_blocked_id_fkey', 'block', 'user', ['blocked_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('follow_following_id_fkey', 'follow', 'user', ['following_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('follow_follower_id_fkey', 'follow', 'user', ['follower_id'], ['id'], ondelete='CASCADE')

    # 5. Modify constraints and KEEP persona_id for ML Context & Rendering (nullable=True)
    op.drop_constraint('comment_persona_id_fkey', 'comment', type_='foreignkey')
    op.alter_column('comment', 'persona_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key('comment_persona_id_fkey_setnull', 'comment', 'persona', ['persona_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('comment_user_id_fkey', 'comment', 'user', ['user_id'], ['id'], ondelete='CASCADE')

    # comment_mention 중복 제거 및 PK 교체
    op.execute("""
        DELETE FROM comment_mention a USING comment_mention b
        WHERE a.comment_id = b.comment_id AND a.user_id = b.user_id AND a.ctid > b.ctid;
    """)
    op.drop_constraint('comment_mention_persona_id_fkey', 'comment_mention', type_='foreignkey')
    op.execute("ALTER TABLE comment_mention DROP CONSTRAINT comment_mention_pkey;")
    op.create_foreign_key('comment_mention_user_id_fkey', 'comment_mention', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.execute("ALTER TABLE comment_mention ADD PRIMARY KEY (comment_id, user_id);")
    op.drop_column('comment_mention', 'persona_id')

    # like_log 중복 제거 (user_id 통합으로 인한 타겟당 1회 초과 좋아요 방지)
    op.execute("""
        DELETE FROM like_log a USING (
            SELECT MIN(id) as id, user_id, target_type, target_id 
            FROM like_log GROUP BY user_id, target_type, target_id HAVING COUNT(*) > 1
        ) b
        WHERE a.user_id = b.user_id 
          AND a.target_type = b.target_type 
          AND a.target_id = b.target_id 
          AND a.id <> b.id;
    """)
    op.drop_constraint('uq_likelog_persona_target', 'like_log', type_='unique')
    op.create_unique_constraint('uq_likelog_user_target', 'like_log', ['user_id', 'target_type', 'target_id'])
    op.drop_constraint('like_log_persona_id_fkey', 'like_log', type_='foreignkey')
    op.alter_column('like_log', 'persona_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key('likelog_persona_id_fkey_setnull', 'like_log', 'persona', ['persona_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('likelog_user_id_fkey', 'like_log', 'user', ['user_id'], ['id'], ondelete='CASCADE')

    op.drop_constraint('post_persona_id_fkey', 'post', type_='foreignkey')
    op.alter_column('post', 'persona_id', existing_type=sa.UUID(), nullable=True)
    op.create_foreign_key('post_persona_id_fkey_setnull', 'post', 'persona', ['persona_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('post_user_id_fkey', 'post', 'user', ['user_id'], ['id'], ondelete='CASCADE')

    # post_mention 중복 제거 및 PK 교체
    op.execute("""
        DELETE FROM post_mention a USING post_mention b
        WHERE a.post_id = b.post_id AND a.user_id = b.user_id AND a.ctid > b.ctid;
    """)
    op.drop_constraint('post_mention_persona_id_fkey', 'post_mention', type_='foreignkey')
    op.execute("ALTER TABLE post_mention DROP CONSTRAINT post_mention_pkey;")
    op.create_foreign_key('post_mention_user_id_fkey', 'post_mention', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.execute("ALTER TABLE post_mention ADD PRIMARY KEY (post_id, user_id);")
    op.drop_column('post_mention', 'persona_id')

    # 6. 프로필 데이터 마이그레이션 (Persona -> User)
    # profile_image_url은 페르소나별 분리를 위해 Persona 테이블에도 유지합니다.
    op.add_column('user', sa.Column('tag', sa.String(length=10), server_default='0000', nullable=False))
    op.add_column('user', sa.Column('profile_image_url', sa.String(length=500), nullable=True))
    op.add_column('user', sa.Column('profile_msg', sa.String(length=200), nullable=True))

    op.execute("""
        UPDATE "user" u
        SET 
            tag = p.tag, 
            profile_image_url = p.profile_image_url, 
            profile_msg = p.profile_msg
        FROM (
            SELECT DISTINCT ON (user_id) user_id, tag, profile_image_url, profile_msg 
            FROM persona
        ) p
        WHERE u.id = p.user_id;
    """)

    # 6.1 User 테이블의 (nickname, tag) 중복 데이터 클렌징
    # 중복되는 조합이 있을 경우 tag를 고유한 형태(id 활용)로 임의 변경하여 Unique 제약조건 충돌 방지
    op.execute("""
        UPDATE "user" 
        SET tag = lpad((abs(hashtext(id::text)) % 10000)::text, 4, '0')
        WHERE id IN (
            SELECT id FROM (SELECT id, row_number() OVER (PARTITION BY nickname, tag ORDER BY id) as rn FROM "user") t WHERE t.rn > 1
        );
    """)
    op.create_unique_constraint('uq_user_nickname_tag', 'user', ['nickname', 'tag'])
    op.create_index('ix_user_nickname_trgm', 'user', ['nickname'], unique=False, postgresql_using='gin', postgresql_ops={'nickname': 'gin_trgm_ops'})

    op.drop_index('ix_persona_nickname_trgm', table_name='persona', postgresql_using='gin', postgresql_ops={'nickname': 'gin_trgm_ops'})
    op.drop_constraint('uq_persona_nickname_tag', 'persona', type_='unique')
    op.drop_column('persona', 'tag')
    op.drop_column('persona', 'profile_msg')

def downgrade() -> None:
    op.add_column('persona', sa.Column('profile_msg', sa.VARCHAR(length=200), autoincrement=False, nullable=True))
    op.add_column('persona', sa.Column('tag', sa.VARCHAR(length=10), server_default='0000', autoincrement=False, nullable=False))
    op.create_unique_constraint('uq_persona_nickname_tag', 'persona', ['nickname', 'tag'])
    op.create_index('ix_persona_nickname_trgm', 'persona', ['nickname'], unique=False, postgresql_using='gin', postgresql_ops={'nickname': 'gin_trgm_ops'})
    op.drop_index('ix_user_nickname_trgm', table_name='user', postgresql_using='gin', postgresql_ops={'nickname': 'gin_trgm_ops'})
    op.drop_constraint('uq_user_nickname_tag', 'user', type_='unique')
    op.drop_column('user', 'profile_msg')
    op.drop_column('user', 'profile_image_url')
    op.drop_column('user', 'tag')

    # Downgrade drops user_id and reverts back to persona_id
    # Note: Downgrade data migration is complex (mapping user back to a persona).
    # This just recreates the schema structure as it was.
    op.drop_column('user', 'deleted_at')
    op.drop_column('user', 'status')
    
    op.add_column('post_mention', sa.Column('persona_id', sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint('post_mention_user_id_fkey', 'post_mention', type_='foreignkey')
    op.create_foreign_key('post_mention_persona_id_fkey', 'post_mention', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.drop_column('post_mention', 'user_id')
    
    op.drop_constraint('post_user_id_fkey', 'post', type_='foreignkey')
    op.drop_constraint('post_persona_id_fkey_setnull', 'post', type_='foreignkey')
    op.execute("DELETE FROM post WHERE persona_id IS NULL;")
    op.alter_column('post', 'persona_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('post_persona_id_fkey', 'post', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.drop_column('post', 'user_id')
    
    op.drop_constraint('likelog_user_id_fkey', 'like_log', type_='foreignkey')
    op.drop_constraint('likelog_persona_id_fkey_setnull', 'like_log', type_='foreignkey')
    op.drop_constraint('uq_likelog_user_target', 'like_log', type_='unique')
    op.create_unique_constraint('uq_likelog_persona_target', 'like_log', ['persona_id', 'target_type', 'target_id'])
    op.execute("DELETE FROM like_log WHERE persona_id IS NULL;")
    op.alter_column('like_log', 'persona_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('like_log_persona_id_fkey', 'like_log', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.drop_column('like_log', 'user_id')
    
    op.drop_constraint('follow_follower_id_fkey', 'follow', type_='foreignkey')
    op.drop_constraint('follow_following_id_fkey', 'follow', type_='foreignkey')
    op.create_foreign_key('follow_follower_id_fkey', 'follow', 'persona', ['follower_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('follow_following_id_fkey', 'follow', 'persona', ['following_id'], ['id'], ondelete='CASCADE')
    
    op.add_column('comment_mention', sa.Column('persona_id', sa.UUID(), autoincrement=False, nullable=True))
    op.drop_constraint('comment_mention_user_id_fkey', 'comment_mention', type_='foreignkey')
    op.create_foreign_key('comment_mention_persona_id_fkey', 'comment_mention', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.drop_column('comment_mention', 'user_id')
    
    op.drop_constraint('comment_user_id_fkey', 'comment', type_='foreignkey')
    op.drop_constraint('comment_persona_id_fkey_setnull', 'comment', type_='foreignkey')
    op.execute("DELETE FROM comment WHERE persona_id IS NULL;")
    op.alter_column('comment', 'persona_id', existing_type=sa.UUID(), nullable=False)
    op.create_foreign_key('comment_persona_id_fkey', 'comment', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.drop_column('comment', 'user_id')
    
    op.drop_constraint('block_blocker_id_fkey', 'block', type_='foreignkey')
    op.drop_constraint('block_blocked_id_fkey', 'block', type_='foreignkey')
    op.create_foreign_key('block_blocked_id_fkey', 'block', 'persona', ['blocked_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('block_blocker_id_fkey', 'block', 'persona', ['blocker_id'], ['id'], ondelete='CASCADE')