from uuid import UUID

from sqlalchemy.orm import Session

from app.schemas.mapper.pagination import PaginationMapper
from app.schemas.request.ml.recommend import MlRecommendRequest
from app.schemas.response.search import PostSearchResponse, SearchPost
from app.service.ml import ml_recommend_service
from app.service.ml.sync import safe_ml_call
from app.service.post.read_post import post_read_service


class ForYouSearchService:
    async def search_for_you(
        self,
        db: Session,
        *,
        user_id: UUID,
        persona_id: UUID | None,
        query: str,
        limit: int,
        search_pattern: str,
        current_user_id: UUID,
    ) -> PostSearchResponse | None:
        ml_result = await safe_ml_call(
            "recommend feed",
            lambda: ml_recommend_service.recommend_feed(
                MlRecommendRequest(
                    user_id=str(user_id),
                    persona_id=str(persona_id) if persona_id else None,
                    query=query,
                    top_k=limit,
                )
            ),
        )
        if ml_result is None:
            return None

        feed_ids: list[int] = []
        for item in ml_result.feeds:
            try:
                feed_ids.append(int(item.feed_id))
            except (TypeError, ValueError):
                continue

        if not feed_ids:
            return PostSearchResponse(
                items=[],
                meta=PaginationMapper.build_cursor_meta(),
            )

        post_items = post_read_service.get_posts_by_ids(db, feed_ids, current_user_id)
        items = [SearchPost(**post.model_dump()) for post in post_items]

        if not items:
            return PostSearchResponse(
                items=[],
                meta=PaginationMapper.build_cursor_meta(),
            )

        return PostSearchResponse(
            items=items,
            meta=PaginationMapper.build_cursor_meta(has_next=False),
        )


for_you_search_service = ForYouSearchService()
