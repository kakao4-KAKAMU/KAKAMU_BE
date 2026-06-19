from typing import Optional, Union
from uuid import UUID

from app.core.config import settings
from app.models import Persona as PersonaModel
from app.schemas.base.persona import Persona


class PersonaMapper:
    @staticmethod
    def _resolve_profile_image_url(value: Optional[str]) -> Optional[str]:
        if not value:
            return value
        if value.startswith("http://") or value.startswith("https://"):
            return value
        if value.startswith("/static"):
            return f"{settings.DEFAULT_IMAGE.rstrip('/')}/{value.lstrip('/')}"
        return f"{settings.IMAGE_SERVER_URL.rstrip('/')}/{value.lstrip('/')}"

    @staticmethod
    def to_persona(persona: PersonaModel) -> Persona:
        return Persona(
            id=persona.id,
            user_id=persona.user_id,
            nickname=persona.nickname,
            profile_image_url=PersonaMapper._resolve_profile_image_url(persona.profile_image_url),
        )
