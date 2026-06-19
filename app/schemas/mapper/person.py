from typing import Optional

from app.models.movie import People
from app.schemas.base.person import Person


class PersonMapper:
    @staticmethod
    def to_person(
        person: People,
        *,
        job: Optional[str] = None,
        profile_image: Optional[str] = None,
    ) -> Person:
        return Person(
            id=person.id,
            name=person.person_name,
            job=job,
            profile_image=profile_image,
        )
