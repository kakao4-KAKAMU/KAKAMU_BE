import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def safe_ml_call(label: str, coro_factory: Callable[[], Awaitable[T]]) -> T | None:
    try:
        return await coro_factory()
    except httpx.HTTPError as exc:
        logger.exception("[ML] %s HTTP 요청 실패: %s", label, exc)
    except Exception as exc:
        logger.exception("[ML] %s 처리 중 오류: %s", label, exc)
    return None
