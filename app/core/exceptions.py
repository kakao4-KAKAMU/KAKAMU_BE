from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.encoders import jsonable_encoder

def setup_exception_handlers(app: FastAPI) -> None:
    """FastAPI 애플리케이션에 전역 예외 처리기를 등록합니다."""
    
    # 1. 커스텀 에러 및 FastAPI 내장 에러 (404, 405 등) 일괄 처리
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # 이미 통일한 딕셔너리 포맷({"code": "...", "message": "..."})인 경우 그대로 반환
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        
        # FastAPI가 자체적으로 발생시키는 단순 문자열 에러를 포맷에 맞게 감싸기
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": {"code": f"HTTP_{exc.status_code}_ERROR", "message": str(exc.detail)}}
        )

    # 2. 데이터 유효성 검사 실패 (422) 에러 일괄 처리
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": {"code": "VALIDATION_ERROR", "message": "요청 데이터 형식이 올바르지 않습니다.", "errors": jsonable_encoder(exc.errors())}}
        )
