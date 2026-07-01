from uuid import UUID


# {mentions, hashtags, *comment_info}
def build_comment_info_redis_key(comment_id: int) -> str:
    return f"kakamu:comment:{comment_id}:info"


# number of likes
def build_comment_liked_count_redis_key(comment_id: int) -> str:
    return f"kakamu:comment:{comment_id}:liked_count"


# number of comments
def build_comment_comment_count_redis_key(comment_id: int) -> str:
    return f"kakamu:comment:{comment_id}:comment_count"


# {is_saved, is_liked}
def build_comment_saved_count_redis_key(comment_id: int, user_id: UUID) -> str:
    return f"kakamu:comment:{comment_id}:{user_id}:status"
