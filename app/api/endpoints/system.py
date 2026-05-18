from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.redis import redis_client
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
def health_check():
    """쿠버네티스 상태 확인용 엔드포인트"""
    return {"status": "healthy", "version": "1.0.0"}

@router.get("/")
def read_root():
    return {"message": "Welcome to KAKAMU_BE Platform"}

# DB 연결 테스트용 엔드포인트
@router.get("/db-test")
def test_db(db: Session = Depends(get_db)):
    try:
        # 실제로 가벼운 쿼리를 날려 커넥션이 진짜 살아있는지 확인
        db.execute(text("SELECT 1"))
        return {"status": "Database connection successful"}
    except Exception as e:
        # DB가 죽었다면 500 에러를 던짐.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed"
        )

@router.get("/redis-test")
async def test_redis():
    try:
        # 이미 상단에서 가져온 redis_client 사용
        await redis_client.set("test_key", "Hello Redis!", ex=60) # 60초 후 만료 예시
        value = await redis_client.get("test_key")
        return {"status": "success", "value": value}
    except Exception as e:
        return {"status": "error", "message": str(e)}
