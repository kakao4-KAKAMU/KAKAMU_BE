from uuid import UUID

# {is_following}
def build_user_follow_status_redis_key(user_id: UUID, target_user_id: UUID) -> str:
    return f"kakamu:user:{user_id}:follow:{target_user_id}"


# {follower_count, following_count, post_count}
def build_user_info_redis_key(user_id: UUID) -> str:
    return f"kakamu:user:{user_id}:info"

