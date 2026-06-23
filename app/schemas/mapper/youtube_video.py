from app.models.movie import YoutubeVideo as YoutubeVideoModel
from app.schemas.base.youtube_video import YoutubeVideo


class YoutubeVideoMapper:
    @staticmethod
    def to_youtube_video(video: YoutubeVideoModel) -> YoutubeVideo:
        return YoutubeVideo(
            movie_id=video.movie_id,
            is_trailer=video.is_trailer,
            language=video.language,
            youtube_video_id=video.youtube_video_id,
        )
