"""update movie models

Revision ID: f918313296ae
Revises: 97d3a93995e1
Create Date: 2026-06-09 09:58:19.215844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f918313296ae'
down_revision: Union[str, None] = '97d3a93995e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
        # PostgreSQL uuid 확장 모듈 활성화
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # 1. 기존 테이블 및 컬럼 이름 변경 (데이터 보존)
    op.rename_table('people', 'person')
    op.alter_column('person', 'name', new_column_name='person_name')

    op.rename_table('movie_genre', 'movie_genre_relation')
    op.rename_table('movie_staff', 'movie_person_relation')
    op.alter_column('movie_person_relation', 'people_id', new_column_name='person_id')

    op.alter_column('genre', 'name', new_column_name='genre_name')

    # movie_title 테이블 분리로 인한 기존 movie.title 인덱스 명시적 삭제 (이름 중복 방지)
    op.drop_index('ix_movie_title_trgm', table_name='movie')

    # 2. 신규 테이블 및 컬럼 추가
    op.create_table('movie_type',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('type', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.add_column('person', sa.Column('person_name_eng', sa.Text(), nullable=True))
    op.add_column('person', sa.Column('kmdb_person_id', sa.Text(), nullable=True))

    op.add_column('movie', sa.Column('nation', sa.Text(), nullable=True))
    op.add_column('movie', sa.Column('kmdb_id', sa.Text(), nullable=True))
    op.add_column('movie', sa.Column('tmdb_id', sa.Text(), nullable=True, comment='TMDB ID'))
    op.add_column('movie', sa.Column('producing_year', sa.Integer(), nullable=True, comment='producing year'))
    op.add_column('movie', sa.Column('movie_type_id', sa.UUID(), nullable=True, comment='movie type id'))
    op.add_column('movie', sa.Column('runtime', sa.Integer(), nullable=True, comment='runtime integer'))
    op.add_column('movie', sa.Column('is_adult', sa.Boolean(), nullable=True, comment='19세 이상 관람 가능 여부'))
    op.add_column('movie', sa.Column('is_rated', sa.Boolean(), nullable=True, comment='심의 데이터 보유 여부'))

    # 기존 job 컬럼 NULL 방지 및 Text 타입으로 변경 (PK 편입을 위해)
    op.execute("UPDATE movie_person_relation SET job = 'Unknown' WHERE job IS NULL;")
    op.execute('ALTER TABLE movie_person_relation ALTER COLUMN job TYPE text USING job::text;')
    op.alter_column('movie_person_relation', 'job', nullable=False)

    # 텍스트 타입으로 기존 타입 명시적 변경
    op.execute('ALTER TABLE movie ALTER COLUMN poster_url TYPE text USING poster_url::text;')
    op.execute('ALTER TABLE movie ALTER COLUMN release_date TYPE text USING release_date::text;')

    # 3. UUID 전환을 위한 매핑 (Integer -> UUID)
    for table in ['movie', 'genre', 'person']:
        op.execute(f'ALTER TABLE {table} ADD COLUMN new_id UUID DEFAULT uuid_generate_v4();')

    fk_mappings = [
        ('fav_movie', 'movie_id', 'movie'),
        ('fav_genre', 'genre_id', 'genre'),
        ('fav_people', 'people_id', 'person'),
        ('post_movie', 'movie_id', 'movie'),
        ('movie_genre_relation', 'movie_id', 'movie'),
        ('movie_genre_relation', 'genre_id', 'genre'),
        ('movie_person_relation', 'movie_id', 'movie'),
        ('movie_person_relation', 'person_id', 'person')
    ]

    for table, col, _ in fk_mappings:
        op.execute(f'ALTER TABLE {table} ADD COLUMN new_{col} UUID;')

    # 3.2 데이터 매핑
    for table, col, ref_table in fk_mappings:
        op.execute(f'UPDATE {table} SET new_{col} = ref.new_id FROM {ref_table} ref WHERE {table}.{col} = ref.id;')

    # 3.3 기존 제약조건 CASCADE 삭제
    op.execute('ALTER TABLE movie DROP CONSTRAINT IF EXISTS movie_pkey CASCADE;')
    op.execute('ALTER TABLE genre DROP CONSTRAINT IF EXISTS genre_pkey CASCADE;')
    op.execute('ALTER TABLE person DROP CONSTRAINT IF EXISTS people_pkey CASCADE;')
    op.execute('ALTER TABLE person DROP CONSTRAINT IF EXISTS person_pkey CASCADE;')

    for table in ['fav_movie', 'fav_genre', 'fav_people', 'post_movie', 'movie_genre_relation', 'movie_person_relation']:
        op.execute(f'ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_pkey CASCADE;')
        if table == 'movie_genre_relation':
            op.execute('ALTER TABLE movie_genre_relation DROP CONSTRAINT IF EXISTS movie_genre_pkey CASCADE;')
        if table == 'movie_person_relation':
            op.execute('ALTER TABLE movie_person_relation DROP CONSTRAINT IF EXISTS movie_staff_pkey CASCADE;')

    # 3.4 기존 Integer 컬럼 삭제
    for table in ['movie', 'genre', 'person']:
        op.drop_column(table, 'id')
    for table, col, _ in fk_mappings:
        op.drop_column(table, col)

    # 3.5 신규 컬럼명 원래 이름으로 변경 및 NOT NULL 설정
    for table in ['movie', 'genre', 'person']:
        op.alter_column(table, 'new_id', new_column_name='id', nullable=False)
    for table, col, _ in fk_mappings:
        op.alter_column(table, f'new_{col}', new_column_name=col, nullable=False)

    # 3.6 PK/FK 재생성
    op.create_primary_key('movie_pkey', 'movie', ['id'])
    op.create_primary_key('genre_pkey', 'genre', ['id'])
    op.create_primary_key('person_pkey', 'person', ['id'])

    op.create_primary_key('fav_movie_pkey', 'fav_movie', ['persona_id', 'movie_id'])
    op.create_primary_key('fav_genre_pkey', 'fav_genre', ['persona_id', 'genre_id'])
    op.create_primary_key('fav_people_pkey', 'fav_people', ['persona_id', 'people_id'])
    op.create_primary_key('post_movie_pkey', 'post_movie', ['post_id', 'movie_id'])
    op.create_primary_key('movie_genre_relation_pkey', 'movie_genre_relation', ['movie_id', 'genre_id'])
    op.create_primary_key('movie_person_relation_pkey', 'movie_person_relation', ['movie_id', 'person_id', 'job'])

    op.create_foreign_key('fav_movie_movie_id_fkey', 'fav_movie', 'movie', ['movie_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fav_genre_genre_id_fkey', 'fav_genre', 'genre', ['genre_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fav_people_people_id_fkey', 'fav_people', 'person', ['people_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('post_movie_movie_id_fkey', 'post_movie', 'movie', ['movie_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('movie_genre_relation_movie_id_fkey', 'movie_genre_relation', 'movie', ['movie_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('movie_genre_relation_genre_id_fkey', 'movie_genre_relation', 'genre', ['genre_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('movie_person_relation_movie_id_fkey', 'movie_person_relation', 'movie', ['movie_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('movie_person_relation_person_id_fkey', 'movie_person_relation', 'person', ['person_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('movie_movie_type_id_fkey', 'movie', 'movie_type', ['movie_type_id'], ['id'])

    # CASCADE 삭제 시 누락될 수 있는 persona_id, post_id 참조 복구
    op.execute('ALTER TABLE fav_movie DROP CONSTRAINT IF EXISTS fav_movie_persona_id_fkey CASCADE;')
    op.create_foreign_key('fav_movie_persona_id_fkey', 'fav_movie', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.execute('ALTER TABLE fav_genre DROP CONSTRAINT IF EXISTS fav_genre_persona_id_fkey CASCADE;')
    op.create_foreign_key('fav_genre_persona_id_fkey', 'fav_genre', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.execute('ALTER TABLE fav_people DROP CONSTRAINT IF EXISTS fav_people_persona_id_fkey CASCADE;')
    op.create_foreign_key('fav_people_persona_id_fkey', 'fav_people', 'persona', ['persona_id'], ['id'], ondelete='CASCADE')
    op.execute('ALTER TABLE post_movie DROP CONSTRAINT IF EXISTS post_movie_post_id_fkey CASCADE;')
    op.create_foreign_key('post_movie_post_id_fkey', 'post_movie', 'post', ['post_id'], ['id'], ondelete='CASCADE')

    # 4. 분리된 신규 테이블(movie_title, overview, youtube_video) 생성
    op.create_table('movie_title',
        sa.Column('movie_id', sa.UUID(), nullable=False),
        sa.Column('title_name', sa.Text(), nullable=False),
        sa.Column('country', sa.Text(), nullable=False),
        sa.Column('is_original', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('movie_id', 'title_name', 'country', 'is_original')
    )
    op.create_index('ix_movie_title_trgm', 'movie_title', ['title_name'], unique=False, postgresql_using='gin', postgresql_ops={'title_name': 'gin_trgm_ops'})
    
    op.create_table('overview',
        sa.Column('movie_id', sa.UUID(), nullable=False),
        sa.Column('platform', sa.Text(), nullable=False),
        sa.Column('lang', sa.Text(), nullable=False),
        sa.Column('overview', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('movie_id', 'platform', 'lang')
    )
    
    op.create_table('youtube_video',
        sa.Column('movie_id', sa.UUID(), nullable=False),
        sa.Column('is_trailer', sa.Boolean(), nullable=False),
        sa.Column('language', sa.Text(), nullable=False),
        sa.Column('youtube_video_id', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['movie_id'], ['movie.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('movie_id', 'youtube_video_id')
    )

    # 5. 기존 데이터 마이그레이션 (movie -> movie_title, overview)
    op.execute("INSERT INTO movie_title (movie_id, title_name, country, is_original) SELECT id, title, 'KR', true FROM movie WHERE title IS NOT NULL;")
    op.execute("INSERT INTO overview (movie_id, platform, lang, overview) SELECT id, 'default', 'ko', overview FROM movie WHERE overview IS NOT NULL;")

    # 6. 불필요해진 기존 컬럼 및 인덱스 삭제
    op.drop_column('movie', 'title')
    op.drop_column('movie', 'overview')
    op.drop_column('movie', 'avg_rating')
    op.drop_column('person', 'profile_image')
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    raise NotImplementedError("데이터 무결성 문제 및 UUID 분할 테이블 구조로 인해 다운그레이드는 지원하지 않습니다.")
    # ### end Alembic commands ###