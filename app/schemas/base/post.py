from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.base.mention import Mention
from app.schemas.base.movie import Movie
from app.schemas.base.user import UserSimpleWithFollow


class ContentBaseObject(BaseModel):
    id: int
    user: UserSimpleWithFollow
    hashtags: List[str]
    mentions: List[Mention]
    like_count: int
    is_liked: bool
    is_saved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class PostItem(ContentBaseObject):
    title: str
    content: str
    image_urls: List[str]
    is_spoiler: bool
    movies: List[Movie]
    comment_count: int
