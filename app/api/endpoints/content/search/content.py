from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.movie import Genre, People, MovieStaff
from app.models.search_log import SearchDailyStat
from app.models.user import User
from app.api.deps.auth import get_optional_user
from app.service.movie.get_movie import movie_read_service
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import (
    GenreListResponse,
    MovieTabSearchResponse,
    PaginatedSearchResponse,
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

    movies = movie_read_service.search_content_tab(
        db,
        search_pattern,
        sort=sort,
        cursor=cursor,
        limit=limit,
    )
    
    items = [
        {"id": m.id, "title": m.titles[0].title_name if m.titles else "제목 없음", "poster_url": m.poster_url}
        for m in movies
    ]
    
    # 커서 페이징은 ID 기반 정렬(accuracy)일 때만 유효함
    next_cursor = str(movies[-1].id) if len(movies) == limit and sort == "accuracy" else None
    return {"status": "success", "items": items, "next_cursor": next_cursor}

# 2. 장르 목록 조회 API
@router.get(
    "/v1/genre/list",
    tags=["Search - Metadata"],
    response_model=GenreListResponse,
    summary="장르 목록 전체 조회"
)
def get_genre_list(db: Session = Depends(get_db)):
    genres = db.query(Genre).order_by(Genre.genre_name.asc()).all()
    return {"status": "success", "genres": [{"id": str(g.id), "name": g.genre_name} for g in genres]}

# 3. 기존 영화 상세 필터 검색 API
@router.get(
    "/v1/search/movie",
    tags=["Search - Metadata"],
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
    movies, total_count = movie_read_service.search_movies(
        db,
        search_pattern=search_pattern,
        genre=genre,
        year=year,
        sort=sort,
        skip=skip,
        limit=limit,
    )
    
    items = [
        {
            "id": str(m.id), 
            "title": m.titles[0].title_name if m.titles else "제목 없음", 
            "release_date": m.release_date, 
            "poster_url": m.poster_url, 
            "avg_rating": 0.0 # avg_rating 컬럼이 삭제되었으므로 응답 호환성을 위해 0.0 처리
        } 
        for m in movies
    ]
    return {"status": "success", "items": items, "skip": skip, "limit": limit, "total_count": total_count}

# 4. 기존 인물 검색 API
@router.get(
    "/v1/search/person",
    tags=["Search - Metadata"],
    response_model=PaginatedSearchResponse,
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
    query = db.query(People)
    if name: 
        query = query.filter(People.person_name.ilike(get_search_pattern(name)))
    if job: 
        query = query.join(MovieStaff, People.id == MovieStaff.people_id).filter(MovieStaff.job.in_(job))
    
    if sort == "name_desc": 
        query = query.order_by(People.person_name.desc(), People.id.desc())
    else: 
        query = query.order_by(People.person_name.asc(), People.id.desc())
        
    total_count = query.count()
    people = query.offset(skip).limit(limit).all()
    # 응답 호환성을 위해 삭제된 profile_image와 분리된 job은 일단 None으로 처리합니다.
    items = [{"id": str(p.id), "name": p.person_name, "profile_image": None, "job": None} for p in people]
    return {"status": "success", "items": items, "skip": skip, "limit": limit, "total_count": total_count}

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
    # 배치가 '어제' 날짜 기준으로 통계를 기록하므로, 어제 날짜를 계산하여 조회
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    
    trends = db.query(SearchDailyStat).filter(
        SearchDailyStat.stat_date == yesterday
    ).order_by(SearchDailyStat.search_count.desc(), SearchDailyStat.id.asc()).limit(limit).all()
    
    items = [
        {"rank": idx + 1, "keyword": t.keyword, "search_count": t.search_count}
        for idx, t in enumerate(trends)
    ]
    
    return {"status": "success", "stat_date": yesterday, "items": items}