from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models import Post, User
from app.schemas.mapper.pagination import PaginationMapper
from app.schemas.request.ml.recommend import MlRecommendRequest
from app.schemas.response.search import PostSearchResponse
from app.service.ml import ml_recommend_service
from app.service.ml.sync import safe_ml_call
from app.service.search.search_service import search_service


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

        posts = (
            db.query(Post, User)
            .join(User, Post.user_id == User.id)
            .filter(
                Post.id.in_(feed_ids),
                Post.status == "ACTIVE",
                User.status == "ACTIVE",
            )
            .options(selectinload(Post.movies))
            .all()
        )
        posts_by_id = {post.id: (post, author) for post, author in posts}
        ordered_posts = [posts_by_id[feed_id] for feed_id in feed_ids if feed_id in posts_by_id]

        if not ordered_posts:
            return PostSearchResponse(
                items=[],
                meta=PaginationMapper.build_cursor_meta(),
            )

        items = search_service._map_posts(db, ordered_posts, current_user_id)
        return PostSearchResponse(
            items=items,
            meta=PaginationMapper.build_cursor_meta(has_next=False),
        )


for_you_search_service = ForYouSearchService()
