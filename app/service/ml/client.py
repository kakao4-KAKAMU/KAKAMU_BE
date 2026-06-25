from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import settings

class MlApiClient:
    """ML 추천/챗봇 서버 HTTP 클라이언트 (OpenAPI base: ML_API_BASE_URL)."""

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        self.base_url = (base_url or settings.ML_API_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self._url(path), params=params)
            response.raise_for_status()
            return response

    async def post(self, path: str, *, json: dict[str, Any] | None = None) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(self._url(path), json=json)
            response.raise_for_status()
            return response

    async def stream_post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> AsyncIterator[bytes]:
        request_timeout = timeout if timeout is not None else self.timeout
        async with httpx.AsyncClient(timeout=request_timeout) as client:
            async with client.stream("POST", self._url(path), json=json) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    yield line.encode("utf-8") + b"\n"


ml_api_client = MlApiClient()
