import logging
import time
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import Post
from app.service.post.read_post import PostReadService
from app.service.post.read_post_new import PostInfoQueryOptions, PostReadServiceNew

logger = logging.getLogger(__name__)

TEST_USER_ID = UUID("e7e0c48a-913f-45a9-89e4-0e11d9c7c868")
TEST_POST_IDS = [20, 22, 21]


@pytest.fixture(scope="function")
def db():
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()


def test_get_post_info_by_ids(db):
    info_map, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(db, TEST_POST_IDS)

    assert info_map
    assert ordered_post_ids
    for post_id in TEST_POST_IDS:
        if post_id not in info_map:
            continue
        row = info_map[post_id]
        assert "post" in row
        assert "author" in row
        assert "mentions" in row
        assert "hashtags" in row
        assert row["post"].id == post_id
        assert isinstance(row["mentions"], list)
        assert isinstance(row["hashtags"], list)


def test_get_post_info_by_ids_with_options(db):
    info_map, ordered_post_ids = PostReadServiceNew.get_post_info_by_ids(
        db,
        options=PostInfoQueryOptions(
            filters=(Post.id.in_(TEST_POST_IDS),),
            order_by=Post.id.desc(),
            limit=3,
        ),
    )

    assert info_map
    assert len(ordered_post_ids) <= 3


def test_get_post_counts_by_ids(db):
    result = PostReadServiceNew.get_post_counts_by_ids(db, TEST_POST_IDS)
    assert result


def test_get_post_status_by_user_and_post_ids(db):
    result = PostReadServiceNew.get_post_status_by_user_and_post_ids(
        db, TEST_USER_ID, TEST_POST_IDS
    )
    assert result


def test_build_post_infos_original(db):
    prs = PostReadService()
    posts = db.query(Post).filter(Post.id.in_(TEST_POST_IDS)).all()
    info_map, _ = PostReadServiceNew.get_post_info_by_ids(db, [post.id for post in posts])
    result = prs._build_post_infos(db, posts, TEST_USER_ID, info_map)
    assert result.mentions_map is not None
    assert result.hashtags_map is not None


def test_build_post_infos_new(db):
    start_cpu = time.process_time()
    result = PostReadServiceNew.build_post_infos(db, TEST_POST_IDS, TEST_USER_ID)
    end_cpu = time.process_time()
    logger.info("new CPU time: %s seconds", end_cpu - start_cpu)
    assert result
