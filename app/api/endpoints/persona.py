from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import re

from app.db.session import get_db
from app.models import Persona

router = APIRouter()

@router.get("/check-nickname")
def check_nickname_duplicate(
    nickname: str = Query(..., description="검사할 닉네임과 태그 조합 (예: 영화광#123A)"),
    db: Session = Depends(get_db)
):
    """
    페르소나 생성/수정 폼에서 닉네임+태그 조합이 사용 가능한지 실시간으로 검사합니다.
    """
    if '#' not in nickname:
        return {"is_available": False, "message": "'닉네임#태그' 형태로 입력하세요."}
        
    name, tag = nickname.split('#', 1)
    
    if not re.fullmatch(r'[A-Za-z0-9]{3,5}', tag):
        return {"is_available": False, "message": "태그는 숫자와 영어 조합의 3~5글자여야 합니다."}
        
    existing_persona = db.execute(
        select(Persona).where(and_(Persona.nickname == name, Persona.tag == tag))
    ).scalar_one_or_none()
    
    if existing_persona:
        return {"is_available": False, "message": "이미 사용 중인 닉네임과 태그 조합입니다."}
        
    return {"is_available": True, "message": "사용 가능한 닉네임입니다."}