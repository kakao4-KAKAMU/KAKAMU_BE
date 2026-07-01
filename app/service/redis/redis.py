import json
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.core.redis import sync_redis_client


class RedisClient:
    def __init__(self):
        self.redis_client = sync_redis_client

    def get(self, key: str, class_type: Type[BaseModel] | None = None) -> Any:
        value = self.redis_client.get(key)
        if value is None:
            return None
        if class_type:
            return class_type.model_validate(json.loads(value))
        return json.loads(value)

    def get_many(
        self, keys: List[str], class_type: Type[BaseModel] | None = None
    ) -> Dict[str, Any]:
        if not keys:
            return {}

        values = self.redis_client.mget(keys)
        result: Dict[str, Any] = {}
        for key, value in zip(keys, values):
            if value is None:
                result[key] = None
                continue
            try:
                if class_type:
                    result[key] = class_type.model_validate(json.loads(value))
                else:
                    result[key] = json.loads(value)
            except Exception:
                result[key] = None
        return result

    def set(self, key: str, value: Any, ex: int | None = None) -> None:
        payload = value if isinstance(value, str) else json.dumps(value)
        if ex is not None:
            self.redis_client.setex(key, ex, payload)
        else:
            self.redis_client.set(key, payload)

    def set_many(self, data: Dict[str, Any]) -> None:
        if not data:
            return
        self.redis_client.mset(
            {
                key: value if isinstance(value, str) else json.dumps(value)
                for key, value in data.items()
            }
        )

    def setex_many(self, data: Dict[str, Any], ex: int) -> None:
        if not data:
            return
        pipe = self.redis_client.pipeline()
        for key, value in data.items():
            payload = value if isinstance(value, str) else json.dumps(value)
            pipe.setex(key, ex, payload)
        pipe.execute()

    def increment(self, key: str) -> int:
        return self.redis_client.incr(key)

    def decrement(self, key: str) -> int:
        return self.redis_client.decr(key)

    def increment_by(self, key: str, amount: int) -> int:
        return self.redis_client.incrby(key, amount)

    def decrement_by(self, key: str, amount: int) -> int:
        return self.redis_client.decrby(key, amount)

    def delete(self, key: str) -> None:
        self.redis_client.delete(key)


redis_client = RedisClient()
