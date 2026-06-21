from enum import StrEnum


class JudgeType(StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"


class ChatMetadataType(StrEnum):
    MOVIE = "movie"
    FEED = "feed"
