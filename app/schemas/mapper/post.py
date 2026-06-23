from typing import List, Optional

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
        is_following: bool,
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
            like_count=post.like_count,
            is_liked=is_liked,
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
        is_following: bool,
    ) -> PostItem:
        return PostMapper._to_post_item(
            post,
            author,
            hashtags=hashtags,
            mentions=mentions,
            movies=[MovieMapper.to_movie(movie) for movie in post.movies],
            comment_count=comment_count,
            is_liked=is_liked,
            is_following=is_following,
        )

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
        is_following: bool,
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
                is_following=is_following,
            ).model_dump()
        )
