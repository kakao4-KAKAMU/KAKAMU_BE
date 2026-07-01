from typing import TypedDict, List

from app.models.post import Post as PostModel
from app.models.user import User as UserModel
from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie

GetPostInfoStruct = TypedDict("GetPostInfoStruct", {
    "post": PostModel,
    "author": UserModel,
    "mentions": List[Mention],
    "hashtags": List[str],
    "movies": List[Movie],
})

GetPostCountsStruct = TypedDict("GetPostCountsStruct", {
    "comment_count": int,
    "like_count": int,
})

GetPostStatusStruct = TypedDict("GetPostStatusStruct", {
    "is_liked": bool,
    "is_saved": bool,
    "is_following": bool,
})

GetPostInfoFullStruct = TypedDict(
    "GetPostInfoFullStruct",
    {
        "post": PostModel,
        "author": UserModel,
        "mentions": List[Mention],
        "hashtags": List[str],
        "movies": List[Movie],
        "comment_count": int,
        "like_count": int,
        "is_liked": bool,
        "is_saved": bool,
        "is_following": bool,
    },
)
