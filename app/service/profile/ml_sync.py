from uuid import UUID

from sqlalchemy.orm import Session

from app.models import FavGenre, FavMovie, FavPeople, Genre, Persona
from app.schemas.request.ml.ingest import (
    MlIngestPersonaDeleteEnvelope,
    MlIngestPersonaDeletePayload,
    MlIngestPersonaEnvelope,
    MlIngestPersonaPayload,
)
from app.schemas.request.profile import PersonaCreate, PersonaEdit
from app.service.ml import ml_ingest_service
from app.service.ml.sync import safe_ml_call


class PersonaMlSyncService:
    def _build_payload(
        self,
        db: Session,
        persona: Persona,
        *,
        label: str | None = None,
        fav_movie_ids: list[UUID] | None = None,
        fav_genre_ids: list[UUID] | None = None,
        fav_people_ids: list[UUID] | None = None,
    ) -> MlIngestPersonaPayload:
        movie_ids = fav_movie_ids
        genre_ids = fav_genre_ids
        people_ids = fav_people_ids

        if movie_ids is None:
            movie_ids = [
                row.movie_id for row in db.query(FavMovie).filter(FavMovie.persona_id == persona.id).all()
            ]
        if genre_ids is None:
            genre_ids = [
                row.genre_id for row in db.query(FavGenre).filter(FavGenre.persona_id == persona.id).all()
            ]
        if people_ids is None:
            people_ids = [
                row.people_id for row in db.query(FavPeople).filter(FavPeople.persona_id == persona.id).all()
            ]

        genre_names: list[str] = []
        if genre_ids:
            genre_names = [
                genre.genre_name
                for genre in db.query(Genre).filter(Genre.id.in_(genre_ids)).all()
            ]

        return MlIngestPersonaPayload(
            persona_id=str(persona.id),
            user_id=str(persona.user_id),
            label=label or persona.nickname,
            genres=genre_names,
            movies=[str(movie_id) for movie_id in movie_ids],
            persons=[str(people_id) for people_id in people_ids],
        )

    async def sync_create(
        self,
        db: Session,
        persona: Persona,
        persona_data: PersonaCreate,
    ) -> None:
        payload = self._build_payload(
            db,
            persona,
            label=persona_data.nickname,
            fav_movie_ids=persona_data.fav_movie_ids,
            fav_genre_ids=persona_data.fav_genre_ids,
            fav_people_ids=persona_data.fav_people_ids,
        )
        envelope = MlIngestPersonaEnvelope(payload=payload)
        await safe_ml_call("ingest persona create", lambda: ml_ingest_service.create_persona(envelope))

    async def sync_update(
        self,
        db: Session,
        persona: Persona,
        persona_data: PersonaEdit,
    ) -> None:
        payload = self._build_payload(
            db,
            persona,
            label=persona_data.nickname or persona.nickname,
            fav_movie_ids=persona_data.fav_movie_ids,
            fav_genre_ids=persona_data.fav_genre_ids,
            fav_people_ids=persona_data.fav_people_ids,
        )
        envelope = MlIngestPersonaEnvelope(payload=payload)
        await safe_ml_call("ingest persona modify", lambda: ml_ingest_service.modify_persona(envelope))

    async def sync_delete(self, persona: Persona) -> None:
        envelope = MlIngestPersonaDeleteEnvelope(
            payload=MlIngestPersonaDeletePayload(
                persona_id=str(persona.id),
                user_id=str(persona.user_id),
            )
        )
        await safe_ml_call("ingest persona delete", lambda: ml_ingest_service.delete_persona(envelope))


persona_ml_sync_service = PersonaMlSyncService()
