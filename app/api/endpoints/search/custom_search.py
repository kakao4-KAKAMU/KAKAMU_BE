from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc, case, func, or_

from app.db.session import get_db
from app.models import Post, Movie, FavGenre, Genre
from .utils import handle_search_request

router = APIRouter()

@router.get("/v1/search")
async def search_contents(
    request: Request,
    background_tasks: BackgroundTasks,
    q: str = Query(..., min_length=1, description="검색어"),
    tab: str = Query(..., description="탐색 탭 (live, for-you)"),
    active_persona_id: UUID = Query(..., description="현재 활성화된 페르소나 ID"),
    cursor: Optional[str] = Query(None, description="페이징 커서 (live: id, for-you: score_id)"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    # 1. 텍스트 매칭 조건 (제목 및 본문 부분 일치 검색)
    search_condition = or_(Post.title.ilike(f"%{q}%"), Post.content.ilike(f"%{q}%"))
    base_query = db.query(Post).filter(Post.status == "ACTIVE", search_condition)

    items = []
    next_cursor = None

    # 2. 탭별 정렬 로직 분기
    if tab == "live":
        # [Live 탭] 최신순 정렬 및 단순 ID 커서 페이징
        if cursor:
            try:
                base_query = base_query.filter(Post.id < int(cursor))
            except (ValueError, TypeError):
                pass  # 잘못된 커서 형식은 무시하고 첫 페이지부터 조회
        
        items = base_query.order_by(desc(Post.created_at), desc(Post.id)).limit(limit).all()
        if len(items) == limit:
            next_cursor = str(items[-1].id)

    elif tab == "for-you":
        # [For You 탭] 스코어 공식 = TextAccuracy*0.4 + LikeCount*0.2 + PersonaPreferenceWeight*0.4
        
        # TextAccuracy 가중치 (정확히 일치하면 1.0, 부분 일치면 0.5 부여)
        text_accuracy = case((Post.title == q, 1.0), else_=0.5)
        
        # [수정] Redis 대신 RDB의 FavGenre를 조회하여 취향 가중치 추출
        fav_genres = db.query(Genre.name).join(
            FavGenre, FavGenre.genre_id == Genre.id
        ).filter(FavGenre.persona_id == active_persona_id).all()
        
        preferred_categories = [g[0] for g in fav_genres]
        
        # 사용자의 선호 장르 카테고리에 포함되면 가중치 부여
        pref_weight = case((Post.category.in_(preferred_categories), 1.0), else_=0.0) if preferred_categories else 0.0
        
        # 최종 점수 계산
        score_calc = (text_accuracy * 0.4) + (Post.like_count * 0.2) + (pref_weight * 0.4)
        score_label = score_calc.label("sort_score")
        
        query_with_score = base_query.add_columns(score_label)

        # 복합 커서 처리 (score + id)
        if cursor:
            try:
                last_score, last_id = map(float, cursor.split("_"))
                query_with_score = query_with_score.filter(
                    (score_calc < last_score) | ((score_calc == last_score) & (Post.id < int(last_id)))
                )
            except (ValueError, TypeError):
                pass  # 잘못된 커서 형식은 무시하고 첫 페이지부터 조회

        # 점수 내림차순, ID 내림차순 정렬
        results = query_with_score.order_by(desc(score_label), desc(Post.id)).limit(limit).all()
        
        items = [row.Post for row in results] # ORM 객체만 추출
        if len(results) == limit:
            last_row = results[-1]
            next_cursor = f"{last_row.sort_score}_{last_row.Post.id}"

    # 3. 예외 처리 (Zero-Result Fallback)
    if not items:
        # 속한 취향 그룹 내 실시간 인기 영화 5건 추천 (Fallback)
        fallback_movies = db.query(Movie).order_by(desc(Movie.avg_rating)).limit(5).all()
        return {"items": fallback_movies, "is_fallback": True, "message": "검색 결과가 없어 인기 영화를 추천합니다."}

    # 4. 검색 성공 시 통합 로깅 함수 호출 (Rate Limit 및 RDB 저장)
    handle_search_request(request, background_tasks, str(active_persona_id), q)

    return {"items": items, "next_cursor": next_cursor, "is_fallback": False}