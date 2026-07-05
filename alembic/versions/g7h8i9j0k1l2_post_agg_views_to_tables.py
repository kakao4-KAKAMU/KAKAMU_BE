"""post aggregate views to physical tables

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-05 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "g7h8i9j0k1l2"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS post_comment_count;")
    op.execute("DROP VIEW IF EXISTS post_movie_agg;")
    op.execute("DROP VIEW IF EXISTS post_mention_agg;")
    op.execute("DROP VIEW IF EXISTS post_hashtag_agg;")

    op.execute(
        """
        CREATE TABLE post_hashtag_agg (
            post_id INTEGER PRIMARY KEY REFERENCES post(id) ON DELETE CASCADE,
            hashtags JSONB NOT NULL DEFAULT '[]'::jsonb
        );
        """
    )
    op.execute(
        """
        CREATE TABLE post_mention_agg (
            post_id INTEGER PRIMARY KEY REFERENCES post(id) ON DELETE CASCADE,
            mentions JSONB NOT NULL DEFAULT '[]'::jsonb
        );
        """
    )
    op.execute(
        """
        CREATE TABLE post_movie_agg (
            post_id INTEGER PRIMARY KEY REFERENCES post(id) ON DELETE CASCADE,
            movies JSONB NOT NULL DEFAULT '[]'::jsonb
        );
        """
    )
    op.execute(
        """
        CREATE TABLE post_comment_count (
            post_id INTEGER PRIMARY KEY REFERENCES post(id) ON DELETE CASCADE,
            comment_count INTEGER NOT NULL DEFAULT 0
        );
        """
    )

    op.execute(
        """
        INSERT INTO post_hashtag_agg (post_id, hashtags)
        SELECT ph.post_id,
               COALESCE(json_agg(h.normalized_keyword), '[]'::json)
          FROM post_hashtag ph
          JOIN hashtag h ON h.id = ph.hashtag_id
         GROUP BY ph.post_id;
        """
    )
    op.execute(
        """
        INSERT INTO post_mention_agg (post_id, mentions)
        SELECT pm.post_id,
               COALESCE(
                   json_agg(
                       json_build_object(
                           'id', u.id,
                           'nickname', u.nickname,
                           'tag', u.tag
                       )
                   ),
                   '[]'::json
               )
          FROM post_mention pm
          JOIN "user" u ON u.id = pm.user_id
         WHERE u.status = 'ACTIVE'
         GROUP BY pm.post_id;
        """
    )
    op.execute(
        """
        INSERT INTO post_movie_agg (post_id, movies)
        SELECT pm.post_id,
               COALESCE(
                   json_agg(
                       json_build_object(
                           'id', m.id,
                           'poster_url', m.poster_url,
                           'release_date', m.release_date,
                           'title', mot.title_name
                       )
                   ),
                   '[]'::json
               )
          FROM post_movie pm
          JOIN movie m ON m.id = pm.movie_id
          JOIN movie_original_title mot ON mot.movie_id = m.id
         GROUP BY pm.post_id;
        """
    )
    op.execute(
        """
        INSERT INTO post_comment_count (post_id, comment_count)
        SELECT c.post_id,
               count(c.id)
          FROM comment c
         WHERE c.status = 'ACTIVE'
         GROUP BY c.post_id;
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS post_comment_count;")
    op.execute("DROP TABLE IF EXISTS post_movie_agg;")
    op.execute("DROP TABLE IF EXISTS post_mention_agg;")
    op.execute("DROP TABLE IF EXISTS post_hashtag_agg;")

    op.execute(
        """
        CREATE OR REPLACE VIEW post_hashtag_agg AS
        SELECT ph.post_id,
               json_agg(h.normalized_keyword) AS hashtags
          FROM post_hashtag ph
          JOIN hashtag h ON h.id = ph.hashtag_id
         GROUP BY ph.post_id;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW post_mention_agg AS
        SELECT pm.post_id,
               json_agg(
                   json_build_object(
                       'id', u.id,
                       'nickname', u.nickname,
                       'tag', u.tag
                   )
               ) AS mentions
          FROM post_mention pm
          JOIN "user" u ON u.id = pm.user_id
         WHERE u.status = 'ACTIVE'
         GROUP BY pm.post_id;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW post_movie_agg AS
        SELECT pm.post_id,
               json_agg(
                   json_build_object(
                       'id', m.id,
                       'poster_url', m.poster_url,
                       'release_date', m.release_date,
                       'title', mot.title_name
                   )
               ) AS movies
          FROM post_movie pm
          JOIN movie m ON m.id = pm.movie_id
          JOIN movie_original_title mot ON mot.movie_id = m.id
         GROUP BY pm.post_id;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE VIEW post_comment_count AS
        SELECT c.post_id,
               count(c.id) AS comment_count
          FROM comment c
         WHERE c.status = 'ACTIVE'
         GROUP BY c.post_id;
        """
    )
