from typing import List, Optional, Dict

from app.models.post import Post as PostModel
from app.models.user import User as UserModel
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie
from app.schemas.base.post import PostItem
from app.schemas.mapper.movie import MovieMapper
from app.schemas.mapper.user import UserMapper
from app.schemas.response.search import SearchPost
from app.service.post.schema.read_post_base import GetPostInfoFullStruct


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
        info_map: Dict[int, GetPostInfoFullStruct],
        ordered_post_ids: List[int],
    ) -> List[PostItem]:
        return [
            PostMapper._to_post_item(
                post=info_map[post_id]["post"],
                author=info_map[post_id]["author"],
                hashtags=info_map[post_id]["hashtags"],
                mentions=info_map[post_id]["mentions"],
                movies=info_map[post_id]["movies"],
                like_count=info_map[post_id]["like_count"],
                comment_count=info_map[post_id]["comment_count"],
                is_liked=info_map[post_id]["is_liked"],
                is_saved=info_map[post_id]["is_saved"],
                is_following=info_map[post_id]["is_following"],
            )
            for post_id in ordered_post_ids
        ]

    @staticmethod
    def to_search_posts(
        info_map: Dict[int, GetPostInfoFullStruct],
        ordered_post_ids: List[int],
    ) -> List[SearchPost]:
        return [
            SearchPost(**item.model_dump())
            for item in PostMapper.to_post_responses(info_map, ordered_post_ids)
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
                like_count=like_count,
                comment_count=comment_count,
                is_liked=is_liked,
                is_saved=is_saved,
                is_following=is_following,
            ).model_dump()
        )
