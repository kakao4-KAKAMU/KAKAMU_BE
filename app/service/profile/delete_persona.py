import redis

from app.core.redis import redis_client
import re
from fastapi import HTTPException, status
from sqlalchemy import select, and_, func, update
from sqlalchemy.orm import Session
from app.models.models import Persona
from app.schemas.profile import PersonaCreate

class PersonaDeleteService:


    @staticmethod
    def delete_persona(db: Session, persona: Persona):

        return None