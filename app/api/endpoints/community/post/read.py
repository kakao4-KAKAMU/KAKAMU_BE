from typing import Optional, Union
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.api.deps import get_current_persona
from app.api.deps.auth import get_active_user, get_optional_user
from app.models.user import User
from app.service.post.read_post import post_read_service
from app.schemas.response.post import PostListResponse, PostResponse
from app.schemas.errors import (
    ERROR_FORBIDDEN_BLOCKED_POST,
    ERROR_POST_NOT_FOUND
)

# [추가] OpenTelemetry trace 임포트
from opentelemetry import trace

router = APIRouter()

# [추가] 현재 모듈에 대한 tracer 인스턴스 획득
tracer = trace.get_tracer(__name__)


@router.get(
    "/",
    response_model=PostListResponse,
    summary="피드(게시물) 무한 스크롤 조회"
)
def get_posts(
        cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"),
        limit: int = Query(20, le=100),
        db: Session = Depends(get_db),
        current_persona_id: Optional[UUID] = Depends(get_current_persona),
        current_user: Optional[User] = Depends(get_optional_user)
):
    """게시물 피드를 무한 스크롤(Cursor-based) 방식으로 조회합니다. (비회원 접근 가능)"""
    user_id = current_user.id if current_user else None

    # [추가] 피드 조회 구간 추적
    with tracer.start_as_current_span("get_posts_feed") as span:
        span.set_attribute("user.id", str(user_id) if user_id else "anonymous")
        span.set_attribute("db.cursor", cursor if cursor is not None else "None")
        span.set_attribute("db.limit", limit)

        try:
            result = post_read_service.get_posts(db, user_id, cursor, limit)
            span.set_status(trace.StatusCode.OK)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise


@router.get(
    "/liked",
    response_model=PostListResponse,
    summary="내가 좋아요한 게시물 목록 조회"
)
def get_my_liked_posts(
        cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"),
        limit: int = Query(20, le=100),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_active_user)
):
    """
    내가(유저 본캐가) 좋아요를 누른 게시물 목록을 조회합니다.
    차단한 사용자의 게시물은 좋아요를 눌렀었더라도 노출되지 않습니다.
    """
    # [추가] 좋아요 게시물 조회 구간 추적
    with tracer.start_as_current_span("get_my_liked_posts") as span:
        span.set_attribute("user.id", str(current_user.id))
        span.set_attribute("db.cursor", cursor if cursor is not None else "None")
        span.set_attribute("db.limit", limit)

        try:
            result = post_read_service.get_my_liked_posts(db, current_user.id, cursor, limit)
            span.set_status(trace.StatusCode.OK)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise


@router.get(
    "/user/{target_user_id}",
    response_model=PostListResponse,
    summary="특정 유저의 게시물 목록 조회"
)
def get_user_posts(
        target_user_id: UUID,
        cursor: Optional[int] = Query(None, description="마지막으로 조회한 게시물의 ID"),
        limit: int = Query(20, le=100),
        db: Session = Depends(get_db),
        current_persona_id: Optional[UUID] = Depends(get_current_persona),
        current_user: Optional[User] = Depends(get_optional_user)
):
    """
    특정 유저(본인 또는 타인)가 작성한 게시물 목록을 조회합니다. (비회원 접근 가능)
    """
    user_id = current_user.id if current_user else None

    # [추가] 특정 유저 게시물 조회 구간 추적
    with tracer.start_as_current_span("get_user_posts") as span:
        span.set_attribute("user.id", str(user_id) if user_id else "anonymous")
        span.set_attribute("target_user.id", str(target_user_id))
        span.set_attribute("db.cursor", cursor if cursor is not None else "None")
        span.set_attribute("db.limit", limit)

        try:
            result = post_read_service.get_user_posts(db, target_user_id, user_id, cursor, limit)
            span.set_status(trace.StatusCode.OK)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise


@router.get(
    "/{post_id}",
    response_model=PostResponse,
    responses={
        403: ERROR_FORBIDDEN_BLOCKED_POST,
        404: ERROR_POST_NOT_FOUND
    },
    summary="게시물 상세 조회"
)
def get_post_detail(
        post_id: int,
        db: Session = Depends(get_db),
        current_persona_id: Optional[UUID] = Depends(get_current_persona),
        current_user: Optional[User] = Depends(get_optional_user)
):
    """
    게시물 상세 내용을 조회합니다. (비회원 접근 가능)
    사용자가 '스포일러 보기'를 클릭해서 들어온 것으로 간주하여 마스킹 없이 원본을 반환합니다.
    """
    user_id = current_user.id if current_user else None

    # [추가] 단건 게시물 상세 조회 구간 추적
    with tracer.start_as_current_span("get_post_detail") as span:
        span.set_attribute("user.id", str(user_id) if user_id else "anonymous")
        span.set_attribute("post.id", post_id)

        try:
            result = post_read_service.get_post_detail(db, post_id, user_id)
            span.set_status(trace.StatusCode.OK)
            return result
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, description=str(e))
            raise