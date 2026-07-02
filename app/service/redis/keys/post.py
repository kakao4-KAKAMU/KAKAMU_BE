from uuid import UUID

# {mentions, hashtags, movies, *post_info}
def build_post_info_redis_key(post_id: int) -> str:
    return f"kakamu:post:{post_id}:info"

# number of likes
def build_post_liked_count_redis_key(post_id: int) -> str:
    return f"kakamu:post:{post_id}:liked_count"

# number of comments
def build_post_comment_count_redis_key(post_id: int) -> str:
    return f"kakamu:post:{post_id}:comment_count"

# {is_saved, is_liked}
def build_post_saved_count_redis_key(post_id: int, user_id: UUID) -> str:
    return f"kakamu:post:{post_id}:{user_id}:status"
