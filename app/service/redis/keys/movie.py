from uuid import UUID


def build_movie_detail_redis_key(movie_id: UUID) -> str:
    return f"kakamu:movie:{movie_id}:detail"


def build_movie_saved_status_redis_key(movie_id: UUID, user_id: UUID) -> str:
    return f"kakamu:movie:{movie_id}:{user_id}:status"