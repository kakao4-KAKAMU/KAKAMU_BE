from typing import Dict, Literal

from app.core.logging import logger
from app.core.redis import sync_redis_client

TargetType = Literal["POST", "COMMENT"]
MIN_LIKE_COUNT = 0

# decr 후 0 미만이면 0으로 보정 (원자적 처리)
REDIS_DECR_WITH_FLOOR_SCRIPT = """
local val = redis.call("decr", KEYS[1])
if val < 0 then
    redis.call("set", KEYS[1], 0)
    return 0
end
return val
"""


def clamp_like_count(value: int) -> int:
    return max(MIN_LIKE_COUNT, value)


def build_like_count_redis_key(target_type: TargetType, target_id: int) -> str:
    return f"kakamu:stat:{target_type.lower()}:{target_id}:likes"


class LikeCountService:
    def resolve_like_counts(
        self,
        target_type: TargetType,
        db_like_counts: Dict[int, int],
    ) -> Dict[int, int]:
        """Redis에 값이 있으면 Redis, 없으면 DB like_count를 그대로 사용합니다."""
        if not db_like_counts:
            return {}

        target_ids = list(db_like_counts.keys())
        keys = [build_like_count_redis_key(target_type, target_id) for target_id in target_ids]

        try:
            redis_values = sync_redis_client.mget(keys)
        except Exception as e:
            logger.warning(f"[Redis Error] Like count read failed: {e}")
            return {tid: clamp_like_count(count) for tid, count in db_like_counts.items()}

        resolved: Dict[int, int] = {}
        for target_id, redis_value in zip(target_ids, redis_values):
            if redis_value is not None:
                resolved[target_id] = clamp_like_count(int(redis_value))
            else:
                resolved[target_id] = clamp_like_count(db_like_counts[target_id])
        return resolved


like_count_service = LikeCountService()
