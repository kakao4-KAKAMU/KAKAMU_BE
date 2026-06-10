from fastapi import APIRouter
from . import chat

# AI 도메인 통합 라우터 (수정됨)
router = APIRouter()

# 챗봇 라우터 연결
router.include_router(chat.router, prefix="/chat", tags=["Chatbot"])