from typing import List, Optional
from uuid import UUID

from app.models.post import Post as PostModel
from app.models.user import User as UserModel
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie
from app.schemas.base.post import PostItem
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.user import UserMapper
from app.schemas.response.search import SearchPost


class PostMapper:
    @staticmethod
    def _to_post_item(
        post: PostModel,
        author: Optional[UserModel],
        *,
        hashtags: List[str],
        mentions: List[Mention],
        movies: List[Movie],
        comment_count: int,
        is_liked: bool,
        is_saved: bool,
        is_following: bool,
        like_count: int | None = None,
    ) -> PostItem:
        is_deleted = not author or author.status == "DELETED"
        return PostItem(
            id=post.id,
            user=UserMapper.to_simple_with_follow(
                author,
                is_following=is_following if not is_deleted else False
            ),
            hashtags=hashtags,
            mentions=mentions,
            like_count=like_count if like_count is not None else (post.like_count or 0),
            is_liked=is_liked,
            is_saved=is_saved,
            created_at=post.created_at,
            updated_at=post.updated_at,
            title=post.title,
            content=post.content or "",
            image_urls=post.image_urls or [],
            is_spoiler=post.is_spoiler == 1,
            movies=movies,
            comment_count=comment_count,
        )

    @staticmethod
    def to_post_response(
        post: PostModel,
        author: UserModel,
        *,
        hashtags: List[str],
        mentions: List[Mention],
        comment_count: int,
        is_liked: bool,
        is_saved: bool,
        is_following: bool,
        like_count: int | None = None,
    ) -> PostItem:
        return PostMapper._to_post_item(
            post,
            author,
            hashtags=hashtags,
            mentions=mentions,
            movies=[MovieMapper.to_movie(movie) for movie in post.movies],
            comment_count=comment_count,
            is_liked=is_liked,
            is_saved=is_saved,
            is_following=is_following,
            like_count=like_count,
        )

    @staticmethod
    def to_post_responses(
        posts_with_author: List[tuple[PostModel, UserModel]],
        *,
        hashtags_map: dict[int, List[str]],
        mentions_map: dict[int, List[Mention]],
        comment_counts_map: dict[int, int],
        like_counts_map: dict[int, int],
        liked_post_ids: set[int],
        saved_post_ids: set[int],
        followed_user_ids: set[UUID],
        force_liked: bool = False,
        force_saved: bool = False,
    ) -> List[PostItem]:
        movies_map = {
            post.id: [MovieMapper.to_movie(movie) for movie in post.movies]
            for post, _ in posts_with_author
        }
        return [
            PostMapper._to_post_item(
                post,
                author,
                hashtags=hashtags_map.get(post.id, []),
                mentions=mentions_map.get(post.id, []),
                movies=movies_map[post.id],
                comment_count=comment_counts_map.get(post.id, 0),
                is_liked=force_liked or post.id in liked_post_ids,
                is_saved=force_saved or post.id in saved_post_ids,
                is_following=post.user_id in followed_user_ids,
                like_count=like_counts_map.get(post.id, post.like_count or 0),
            )
            for post, author in posts_with_author
        ]

    @staticmethod
    def to_search_post(
        post: PostModel,
        author: UserModel,
        *,
        hashtags: List[str],
        mentions: List[Mention],
        movies: List[Movie],
        comment_count: int,
        is_liked: bool,
        is_saved: bool,
        is_following: bool,
        like_count: int | None = None,
    ) -> SearchPost:
        return SearchPost(
            **PostMapper._to_post_item(
                post,
                author,
                hashtags=hashtags,
                mentions=mentions,
                movies=movies,
                comment_count=comment_count,
                is_liked=is_liked,
                is_saved=is_saved,
                is_following=is_following,
                like_count=like_count,
            ).model_dump()
        )
