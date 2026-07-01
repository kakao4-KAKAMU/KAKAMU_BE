# 모든 API 요청/응답 공통 로그

import time
import uuid # 모든 로그에 고유한 id 부여

from fastapi import Request # fastapi로 들어오는 모든 요청
from starlette.middleware.base import BaseHTTPMiddleware # 커스텀 로그 미들웨어 생성을 위한

from app.core.logging import logger

# BaseHTTPMiddleware를 상속받는 커스텀 클래스 LoggingMiddleware 생성
class LoggingMiddleware(BaseHTTPMiddleware):
    # request : 현재 들어온 요청
    # call_next : request 요청을 다음 단계로 넘겨주는 함수
    async def dispatch(self, request: Request, call_next):
        import os
        disable_log = os.getenv("DISABLE_ACCESS_LOG", "false").lower() == "true"
        if disable_log:
            return await call_next(request)

        request_id = str(uuid.uuid4()) # 고유한 랜덤 ID 생성
        start_time = time.time() # 요청이 들어온 시간

        logger.info( # 일반 정보 로그를 남김
            "request_started", # 추후에 api에 맞게 커스텀 필요
            extra={
                "extra_data": {
                    "event": "request_started", # 추후에 api에 맞게 커스텀 필요
                    "request_id": request_id, # 고유 ID 매핑
                    "method": request.method, # HTTP 메서드 (GET, POST, PUT, DELETE)
                    "path": request.url.path, # 사용자가 요청한 API 경로
                    "query_params": str(request.query_params),
                    "client_ip": request.client.host if request.client else None, # 요청을 보낸 클라이언트 IP
                }
            },
        )

        try:
            response = await call_next(request) # 요청을 실제 API 핸들러로 넘겨주고 기다린 다음에 응답을 받아옴

            # 걸린 시간을 계산함, 밀리초 단위
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # response.status_code 는 서비스 패키지 로직에서 raise HTTPException에 작성한 상태 코드임.
            if response.status_code >= 500:
                log_method = logger.error
            elif response.status_code >= 400:
                log_method = logger.warning
            else:
                log_method = logger.info

            log_method(
                "request_completed", # 추후에 api에 맞게 커스텀 필요
                extra={
                    "extra_data": {
                        "event": "request_completed", # 추후에 api에 맞게 커스텀 필요
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code, # API가 돌려준 HTTP 상태 코드
                        "latency_ms": latency_ms, # 걸린 시간
                    }
                },
            )

            response.headers["X-Request-ID"] = request_id # 사용자가 받는 응답에 요청의 고유 id를 심어줌
            # 에러 발생시 이 id로 바로 로그 찾기 가능
            return response # 완성된 응답을 클라이언트로 반환

        except Exception as e:
            # 에러 발생 전까지 걸린 시간
            latency_ms = round((time.time() - start_time) * 1000, 2)

            # 에러가 발생했으니깐 error 레벨로 작성
            logger.error(
                "request_failed", # 추후에 api에 맞게 커스텀 필요
                extra={
                    "extra_data": {
                        "event": "request_failed", # 추후에 api에 맞게 커스텀 필요
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": 500, # 상태 코드
                        "latency_ms": latency_ms,
                        "exception_type": type(e).__name__, # exception 타입
                        "error_message" : str(e) # 에러 메시지
                    }
                },
                # exc_info=True, # 에러의 상세한 추적 이력 우선 제외 추후 traceback은 따로 저장
            )

            raise