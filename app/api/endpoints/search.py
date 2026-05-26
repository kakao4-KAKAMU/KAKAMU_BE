from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import extract
from typing import Optional, List

from app.db.session import get_db
from app.models.movie import Movie, Genre, People

router = APIRouter()

# 1. 장르 목록 조회 API
@router.get("/genre/list")
def get_genre_list(db: Session = Depends(get_db)):
    """
    모든 영화 장르 목록을 조회합니다.
    """
    genres = db.query(Genre).order_by(Genre.name.asc()).all()
    return {
        "status": "success",
        "genres": [{"id": g.id, "name": g.name} for g in genres]
    }

# 2. 영화 검색 API
@router.get("/search/movie")
def search_movies(
    name: Optional[str] = Query(None, description="검색할 영화 제목 키워드"),
    genre: Optional[List[int]] = Query(None, description="필터링할 장르 ID 목록 (예: ?genre=1&genre=2)"),
    year: Optional[int] = Query(None, description="개봉 연도 필터"),
    sort: str = Query("year", description="정렬 기준 (year 또는 name)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    조건에 맞는 영화를 검색합니다.
    """
    query = db.query(Movie)

    # [필터] 영화 제목
    if name:
        query = query.filter(Movie.title.ilike(f"%{name}%"))
        
    # [필터] 개봉 연도
    if year:
        query = query.filter(extract('year', Movie.release_date) == year)

    # [필터] 장르 선택
    if genre:
        query = query.join(Movie.genres).filter(Genre.id.in_(genre))

    # [정렬]
    if sort == "name":
        query = query.order_by(Movie.title.asc())
    else:
        query = query.order_by(Movie.release_date.desc()) # 최신 연도순
            
    movies = query.offset(skip).limit(limit).all()
    
    items = [{
        "id": m.id,
        "title": m.title,
        "release_date": m.release_date,
        "poster_url": m.poster_url,
        "avg_rating": float(m.avg_rating) if m.avg_rating else 0.0
    } for m in movies]
        
    return {"status": "success", "items": items, "skip": skip, "limit": limit}

# 3. 인물(배우/감독) 검색 API
@router.get("/search/person")
def search_people(
    name: Optional[str] = Query(None, description="검색할 인물 이름 키워드"),
    job: Optional[List[str]] = Query(None, description="직업 필터 (예: ?job=ACTOR&job=DIRECTOR)"),
    sort: str = Query("name", description="정렬 기준 (name)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    조건에 맞는 인물(배우/감독)을 검색합니다.
    """
    query = db.query(People)
    
    if name:
        query = query.filter(People.name.ilike(f"%{name}%"))
    if job:
        query = query.filter(People.job.in_(job))
    if sort == "name":
        query = query.order_by(People.name.asc())
            
    people = query.offset(skip).limit(limit).all()
    items = [{"id": p.id, "name": p.name, "profile_image": p.profile_image, "job": p.job} for p in people]
        
    return {"status": "success", "items": items, "skip": skip, "limit": limit}