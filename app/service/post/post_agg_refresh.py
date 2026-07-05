from sqlalchemy import text
from sqlalchemy.orm import Session


class PostAggRefreshService:
    """post relation aggregate 테이블을 post_id 단위로 갱신합니다."""

    @staticmethod
    def refresh_hashtag_agg(db: Session, post_id: int) -> None:
        db.execute(
            text(
                """
                INSERT INTO post_hashtag_agg (post_id, hashtags)
                SELECT :post_id,
                       COALESCE(
                           (SELECT json_agg(h.normalized_keyword)
                              FROM post_hashtag ph
                              JOIN hashtag h ON h.id = ph.hashtag_id
                             WHERE ph.post_id = :post_id),
                           '[]'::json
                       )
                ON CONFLICT (post_id) DO UPDATE
                SET hashtags = EXCLUDED.hashtags
                """
            ),
            {"post_id": post_id},
        )

    @staticmethod
    def refresh_mention_agg(db: Session, post_id: int) -> None:
        db.execute(
            text(
                """
                INSERT INTO post_mention_agg (post_id, mentions)
                SELECT :post_id,
                       COALESCE(
                           (SELECT json_agg(
                               json_build_object(
                                   'id', u.id,
                                   'nickname', u.nickname,
                                   'tag', u.tag
                               )
                           )
                              FROM post_mention pm
                              JOIN "user" u ON u.id = pm.user_id
                             WHERE pm.post_id = :post_id
                               AND u.status = 'ACTIVE'),
                           '[]'::json
                       )
                ON CONFLICT (post_id) DO UPDATE
                SET mentions = EXCLUDED.mentions
                """
            ),
            {"post_id": post_id},
        )

    @staticmethod
    def refresh_movie_agg(db: Session, post_id: int) -> None:
        db.execute(
            text(
                """
                INSERT INTO post_movie_agg (post_id, movies)
                SELECT :post_id,
                       COALESCE(
                           (SELECT json_agg(
                               json_build_object(
                                   'id', m.id,
                                   'poster_url', m.poster_url,
                                   'release_date', m.release_date,
                                   'title', mot.title_name
                               )
                           )
                              FROM post_movie pm
                              JOIN movie m ON m.id = pm.movie_id
                              JOIN movie_original_title mot ON mot.movie_id = m.id
                             WHERE pm.post_id = :post_id),
                           '[]'::json
                       )
                ON CONFLICT (post_id) DO UPDATE
                SET movies = EXCLUDED.movies
                """
            ),
            {"post_id": post_id},
        )

    @staticmethod
    def refresh_comment_count(db: Session, post_id: int) -> None:
        db.execute(
            text(
                """
                INSERT INTO post_comment_count (post_id, comment_count)
                SELECT :post_id,
                       COALESCE(
                           (SELECT count(c.id)
                              FROM comment c
                             WHERE c.post_id = :post_id
                               AND c.status = 'ACTIVE'),
                           0
                       )
                ON CONFLICT (post_id) DO UPDATE
                SET comment_count = EXCLUDED.comment_count
                """
            ),
            {"post_id": post_id},
        )

    @classmethod
    def refresh_post(cls, db: Session, post_id: int) -> None:
        cls.refresh_hashtag_agg(db, post_id)
        cls.refresh_mention_agg(db, post_id)
        cls.refresh_movie_agg(db, post_id)
        cls.refresh_comment_count(db, post_id)

    @classmethod
    def delete_post(cls, db: Session, post_id: int) -> None:
        db.execute(text("DELETE FROM post_hashtag_agg WHERE post_id = :post_id"), {"post_id": post_id})
        db.execute(text("DELETE FROM post_mention_agg WHERE post_id = :post_id"), {"post_id": post_id})
        db.execute(text("DELETE FROM post_movie_agg WHERE post_id = :post_id"), {"post_id": post_id})
        db.execute(text("DELETE FROM post_comment_count WHERE post_id = :post_id"), {"post_id": post_id})


post_agg_refresh_service = PostAggRefreshService()
