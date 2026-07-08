from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.models.user import User
from app.api.deps.auth import get_optional_user
from app.service.movie.get_movie import movie_read_service
from app.service.search import search_service
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import (
    GenreListResponse,
    MovieFilterSearchResponse,
    MovieTabSearchResponse,
    PersonFilterSearchResponse,
    TrendSearchResponse,
)

router = APIRouter()

# 1. 콘텐츠(영화) 메인 탭 검색
@router.get(
    "/v1/search/content",
    tags=["Search - Tabs"],
    response_model=MovieTabSearchResponse,
    summary="콘텐츠(영화) 탭 통합 검색"
)
def search_content(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서(ID)"),
    limit: int = Query(20, le=50),
    sort: str = Query("accuracy", description="정렬 기준 (accuracy: 정확도순, popularity: 인기순, latest: 최신순, name_asc: 이름 오름차순, name_desc: 이름 내림차순)"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    user_id = str(current_user.id) if current_user else "anonymous"
    handle_search_request(request, background_tasks, user_id, q)
    search_pattern = get_search_pattern(q)

    return movie_read_service.search_content_tab_response(
        db,
        search_pattern,
        search_query=q,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )

# 2. 장르 목록 조회 API
@router.get(
    "/v1/genre/list",
    tags=["Search - Metadata"],
    response_model=GenreListResponse,
    summary="장르 목록 전체 조회"
)
def get_genre_list(db: Session = Depends(get_db)):
    return search_service.get_genre_list(db)

# 3. 기존 영화 상세 필터 검색 API
@router.get(
    "/v1/search/movie",
    tags=["Search - Metadata"],
    response_model=MovieFilterSearchResponse,
    summary="영화 상세 필터 검색"
)
def search_movies(
    name: Optional[str] = Query(None),
    genre: Optional[List[UUID]] = Query(None),
    year: Optional[int] = Query(None),
    sort: str = Query("year_desc", description="정렬 기준 (year_desc: 최신연도순, year_asc: 과거연도순, name_asc: 이름 오름차순, name_desc: 이름 내림차순)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    search_pattern = get_search_pattern(name) if name else None
    return movie_read_service.search_movies_response(
        db,
        search_pattern=search_pattern,
        genre=genre,
        year=year,
        sort=sort,
        skip=skip,
        limit=limit,
    )

# 4. 기존 인물 검색 API
@router.get(
    "/v1/search/person",
    tags=["Search - Metadata"],
    response_model=PersonFilterSearchResponse,
    summary="영화인 상세 검색"
)
def search_people(
    name: Optional[str] = Query(None),
    job: Optional[List[str]] = Query(None),
    sort: str = Query("name_asc", description="정렬 기준 (name_asc: 이름 오름차순, name_desc: 이름 내림차순)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    search_pattern = get_search_pattern(name) if name else None
    return search_service.search_people(
        db,
        search_pattern=search_pattern,
        jobs=job,
        sort=sort,
        skip=skip,
        limit=limit,
    )

# 5. 일간 인기 검색어(트렌드) Top 10 조회 API
@router.get(
    "/v1/search/trend",
    tags=["Search - Metadata"],
    response_model=TrendSearchResponse,
    summary="인기 검색어(트렌드) Top 10 조회"
)
def get_top_search_keywords(
    limit: int = Query(10, le=50, description="가져올 인기 검색어 개수"),
    db: Session = Depends(get_db)
):
    return search_service.get_trend_keywords(db, limit=limit)
