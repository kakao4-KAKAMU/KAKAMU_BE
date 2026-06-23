from uuid import UUID

from pydantic import BaseModel


class YoutubeVideo(BaseModel):
    movie_id: UUID
    is_trailer: bool
    language: str
    youtube_video_id: str
