from app.models.movie import Genre as GenreModel
from app.schemas.base.genre import Genre


class GenreMapper:
    @staticmethod
    def to_genre(genre: GenreModel) -> Genre:
        return Genre(id=genre.id, name=genre.genre_name)
