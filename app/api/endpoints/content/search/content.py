from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import extract, and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.movie import Movie, Genre, People, MovieTitle, MovieStaff
from app.models.search_log import SearchDailyStat
from app.api.deps import get_active_user
from .utils import handle_search_request, get_search_pattern
from app.schemas.response.search import GenreListResponse, PaginatedSearchResponse, TrendSearchResponse

router = APIRouter()

# 1. 콘텐츠(영화) 메인 탭 검색
@router.get("/v1/search/content", tags=["Search - Tabs"])
def search_content(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    cursor: Optional[str] = Query(None, description="페이징 커서(ID)"),
    limit: int = Query(20, le=50),
    sort: str = Query("accuracy", description="정렬 기준 (accuracy: 정확도순, popularity: 인기순, latest: 최신순, name_asc: 이름 오름차순, name_desc: 이름 내림차순)"),
    user = Depends(get_active_user),
    db: Session = Depends(get_db)
):
    handle_search_request(request, background_tasks, None, q)
    search_pattern = get_search_pattern(q)

    # 서브쿼리(EXISTS)를 사용해 중복 조회 방지
    query = db.query(Movie).filter(Movie.titles.any(MovieTitle.title_name.ilike(search_pattern)))

    # 정렬 기준 적용
    if sort == "popularity":
        # avg_rating 삭제됨에 따라 제작연도를 인기순의 대체 기준으로 활용
        query = query.order_by(Movie.producing_year.desc().nullslast(), Movie.id.desc())
    elif sort == "latest":
        query = query.order_by(Movie.release_date.desc().nullslast(), Movie.id.desc())
    elif sort in ("name_asc", "name_desc"):
        query = query.outerjoin(MovieTitle, and_(Movie.id == MovieTitle.movie_id, MovieTitle.is_original == True))
        if sort == "name_asc":
            query = query.order_by(MovieTitle.title_name.asc(), Movie.id.desc())
        else:
            query = query.order_by(MovieTitle.title_name.desc(), Movie.id.desc())
    else: # accuracy (정확도순) - 현재는 기본값으로 최신순을 사용
        if cursor: 
            query = query.filter(Movie.id < cursor)
        query = query.order_by(Movie.id.desc())
        
    movies = query.options(selectinload(Movie.titles)).limit(limit).all()
    
    items = [
        {"id": str(m.id), "title": m.titles[0].title_name if m.titles else "제목 없음", "poster_url": m.poster_url} 
        for m in movies
    ]
    
    # 커서 페이징은 ID 기반 정렬(accuracy)일 때만 유효함
    next_cursor = str(movies[-1].id) if len(movies) == limit and sort == "accuracy" else None
    return {"status": "success", "items": items, "next_cursor": next_cursor}

# 2. 장르 목록 조회 API
@router.get("/v1/genre/list", tags=["Search - Metadata"], response_model=GenreListResponse)
def get_genre_list(db: Session = Depends(get_db)):
    genres = db.query(Genre).order_by(Genre.genre_name.asc()).all()
    return {"status": "success", "genres": [{"id": str(g.id), "name": g.genre_name} for g in genres]}

# 3. 기존 영화 상세 필터 검색 API
@router.get("/v1/search/movie", tags=["Search - Metadata"])
def search_movies(
    name: Optional[str] = Query(None),
    genre: Optional[List[UUID]] = Query(None),
    year: Optional[int] = Query(None),
    sort: str = Query("year_desc", description="정렬 기준 (year_desc: 최신연도순, year_asc: 과거연도순, name_asc: 이름 오름차순, name_desc: 이름 내림차순)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(Movie).options(selectinload(Movie.titles))
    if name: 
        query = query.filter(Movie.titles.any(MovieTitle.title_name.ilike(get_search_pattern(name))))
    if year: 
        query = query.filter(extract('year', Movie.release_date) == year)
    if genre: 
        query = query.join(Movie.genres).filter(Genre.id.in_(genre))
    
    # 모든 정렬에 결정적 정렬(Deterministic Sorting)을 위한 보조키 id.desc() 추가
    if sort in ("name_asc", "name_desc"):
        query = query.outerjoin(MovieTitle, and_(Movie.id == MovieTitle.movie_id, MovieTitle.is_original == True))
        if sort == "name_asc": 
            query = query.order_by(MovieTitle.title_name.asc(), Movie.id.desc())
        else: 
            query = query.order_by(MovieTitle.title_name.desc(), Movie.id.desc())
    elif sort == "year_asc": 
        query = query.order_by(Movie.release_date.asc().nullslast(), Movie.id.desc())
    else: 
        query = query.order_by(Movie.release_date.desc().nullslast(), Movie.id.desc())
            
    total_count = query.count()
    movies = query.offset(skip).limit(limit).all()
    
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
@router.get("/v1/search/person", tags=["Search - Metadata"], response_model=PaginatedSearchResponse)
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
@router.get("/v1/search/trend", tags=["Search - Metadata"], response_model=TrendSearchResponse)
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