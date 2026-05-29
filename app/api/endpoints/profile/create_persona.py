from fastapi import APIRouter, Depends, HTTPException, status,File, Form, UploadFile
from typing import Optional, List
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.profile import PersonaCreate, PersonaResponse
from app.models import User

from app.service.profile import PersonaService

router = APIRouter()


@router.post("/persona", response_model=PersonaResponse, status_code=201)
async def new_persona_profile(
        nickname: str = Form(...),
        profile_msg: str = Form(""),
        fav_movie_ids: Optional[List[int]] = Form(None),
        fav_genre_ids: Optional[List[int]] = Form(None),
        fav_people_ids: Optional[List[int]] = Form(None),
        profile_image: Optional[UploadFile] = File(None),


        user: User = Depends(get_current_user), # 현재 액세스 토큰으로 인증된 user 정보
        db: Session = Depends(get_db) # db 연결 후 세션 객체
):
    persona_data = PersonaCreate(
        nickname=nickname,
        profile_msg=profile_msg,
        fav_movie_ids=fav_movie_ids,
        fav_genre_ids=fav_genre_ids,
        fav_people_ids=fav_people_ids,
    )

    return await PersonaService.create_new_persona(db=db,
                                                   persona_data=persona_data,
                                                   user_id=user.id,
                                                   profile_image=profile_image)
