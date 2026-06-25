import json
from collections.abc import AsyncIterator
from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.base.movie import Movie
from app.schemas.base.post import PostItem
from app.service.movie.get_movie import movie_read_service
from app.service.post.read_post import post_read_service


class ChatStreamEnrichmentService:
    def __init__(self, db: Session, user_id: UUID):
        self._db = db
        self._user_id = user_id
        self._buffer = b""
        self._event_type: str | None = None

    def _parse_metadata_ids(
        self, metadata: list[dict]
    ) -> tuple[list[int], list[UUID]]:
        feed_ids: list[int] = []
        movie_ids: list[UUID] = []

        for item in metadata:
            meta_type = item.get("type")
            raw_id = item.get("id")
            if not raw_id:
                continue

            if meta_type == "feed":
                try:
                    feed_ids.append(int(raw_id))
                except (TypeError, ValueError):
                    continue
            elif meta_type == "movie":
                try:
                    movie_ids.append(UUID(str(raw_id)))
                except (TypeError, ValueError):
                    continue

        return feed_ids, movie_ids

    def _enrich_generate_reply(self, generate_reply: dict) -> dict:
        metadata = generate_reply.get("reply_metadata") or generate_reply.get("metadata") or []
        if not isinstance(metadata, list):
            metadata = []

        feed_ids, movie_ids = self._parse_metadata_ids(metadata)
        feed_list: list[PostItem] = post_read_service.get_posts_by_ids(
            self._db, feed_ids, self._user_id
        )
        movie_list: list[Movie] = movie_read_service.get_movies_by_ids(
            self._db, movie_ids
        )

        return {
            "reply": generate_reply.get("reply", ""),
            "feed_list": [item.model_dump(mode="json") for item in feed_list],
            "movie_list": [item.model_dump(mode="json") for item in movie_list],
        }

    def _is_node_event(self, payload: dict, event_type: str | None) -> bool:
        return payload.get("type") == "node" or event_type == "node"

    def _apply_generate_reply_enrichment(self, payload: dict, event_type: str | None) -> bool:
        if not self._is_node_event(payload, event_type):
            return False

        for key in ("data", "Data"):
            data = payload.get(key)
            if not isinstance(data, dict):
                continue

            nested = data.get("generate_reply")
            if isinstance(nested, dict):
                data["generate_reply"] = self._enrich_generate_reply(nested)
                payload[key] = data
                return True

            if "reply_metadata" in data or "metadata" in data or "reply" in data:
                payload[key] = {"generate_reply": self._enrich_generate_reply(data)}
                return True

        nested = payload.get("generate_reply")
        if isinstance(nested, dict):
            payload["generate_reply"] = self._enrich_generate_reply(nested)
            return True

        return False

    def _process_sse_line(self, line: bytes) -> bytes:
        if line.startswith(b"event:"):
            self._event_type = line[6:].strip().decode("utf-8", errors="replace") or None
            return line

        if not line.startswith(b"data:"):
            return line

        raw = line[5:].lstrip()
        if not raw:
            return line

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return line

        if not isinstance(payload, dict):
            return line

        if self._apply_generate_reply_enrichment(payload, self._event_type):
            return b"data: " + json.dumps(payload, ensure_ascii=False).encode("utf-8")

        return line

    async def enrich_stream(self, source: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        async for chunk in source:
            self._buffer += chunk
            while b"\n" in self._buffer:
                line, self._buffer = self._buffer.split(b"\n", 1)
                line = line.rstrip(b"\r")

                if not line.strip():
                    self._event_type = None
                    yield b"\n"
                    continue

                yield self._process_sse_line(line) + b"\n"

        if self._buffer:
            line = self._buffer.rstrip(b"\r\n")
            if line:
                yield self._process_sse_line(line) + b"\n"
            self._buffer = b""
