from app.core.logging import logger
import time
from fastapi import BackgroundTasks, HTTPException, Request
from typing import Optional
from app.db.session import SessionLocal
from app.models.search_log import SearchLog
from app.utils.trgm_search import build_ilike_pattern

# 인메모리 Rate Limit 저장소: { "client_id": [timestamp1, timestamp2, ...] }
_rate_limit_store = {}
_last_cleanup_time = time.time()
RATE_LIMIT_WINDOW = 1.0  # 1초 기준
RATE_LIMIT_MAX_REQUESTS = 200  # 1초당 최대 허용 횟수

search_log_buffer = []

def check_rate_limit(client_identifier: str):
    """인메모리 기반 단시간 검색 트래픽 도배 방지 (Rate Limiter)"""
    global _last_cleanup_time
    current_time = time.time()

    # 1. 1분 주기로 접속이 없는 오래된 식별자(Key)를 메모리에서 정리 (Memory Leak 방지)
    if current_time - _last_cleanup_time > 60:
        stale_keys = [
            k for k, v in _rate_limit_store.items() 
            if not v or (current_time - v[-1]) > RATE_LIMIT_WINDOW
        ]
        for k in stale_keys:
            del _rate_limit_store[k]
        _last_cleanup_time = current_time

    # 2. 클라이언트 요청 기록 가져오기 및 윈도우(1초) 밖의 과거 요청 기록 제거
    requests = [req_time for req_time in _rate_limit_store.get(client_identifier, []) if current_time - req_time < RATE_LIMIT_WINDOW]

    # 3. 최대 허용치(5회) 초과 검사
    if len(requests) >= RATE_LIMIT_MAX_REQUESTS:
        _rate_limit_store[client_identifier] = requests  # 정리된 배열 갱신
        raise HTTPException(status_code=429, detail={"code": "RATE_LIMIT_EXCEEDED", "message": "단시간에 너무 많은 검색을 요청했습니다. 잠시 후 다시 시도해주세요."})

    # 4. 현재 요청 시간 기록
    requests.append(current_time)
    _rate_limit_store[client_identifier] = requests

def insert_search_log_background(user_id: Optional[str], keyword: str):
    """API 응답 후 백그라운드에서 실행될 RDB Insert 전용 워커"""
    # 주의: API 응답 시점에 기존 get_db 세션이 닫히므로, 백그라운드용 새 세션을 엽니다.
    db = SessionLocal()
    try:
        # 최대 100자로 잘라내어 DB 저장 (악성 도배 방지)
        safe_keyword = keyword.strip()[:100]
        if not safe_keyword:
            return
        search_log_buffer.append(SearchLog(user_id=user_id, keyword=safe_keyword))
        if len(search_log_buffer) >= 100: # 100개 이상 버퍼링되면 저장
            search_log_buffer
            db.add_all(search_log_buffer)
            search_log_buffer[:] = []
            db.commit()

    except Exception as e:
        db.rollback()
        logger.error(f"Search log insert error: {e}")
    finally:
        db.close()

def handle_search_request(request: Request, background_tasks: BackgroundTasks, user_id: Optional[str], q: str):
    """통합 검색 공통 전처리 (비동기 데이터 적재 및 방어 로직)"""
    client_ip = request.client.host if request.client else "unknown"
    client_id = str(user_id) if user_id else f"IP:{client_ip}"
    check_rate_limit(client_id)

    # API 속도에 전혀 영향을 주지 않고 백그라운드 큐에 작업을 위임
    # background_tasks.add_task(insert_search_log_background, user_id, q)

def get_search_pattern(q: str) -> str:
    """검색어 패턴 생성 (양방향 부분 일치)"""
    return build_ilike_pattern(q)
