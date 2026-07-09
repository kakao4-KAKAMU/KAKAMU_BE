from opentelemetry import trace
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.logging import logger

tracer = trace.get_tracer(__name__)

# 1. settings.DATABASE_URL을 사용하여 엔진 생성
# (settings.py에서 이미 POSTGRES_SERVER 등을 읽어 URL을 만들었으므로 이를 믿고 사용합니다.)
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=50,           # 동시 연결 수 상향
    max_overflow=50,
    pool_recycle=3600,
    pool_pre_ping=True      # 연결 유효성 체크 (네트워크 불안정 대비)
)

# 2. SessionLocal 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. 의존성 주입을 위한 DB 세션 함수
def get_db():
    with tracer.start_as_current_span("db.get_session") as span:
        db = SessionLocal()
        try:
            yield db
        except Exception as e:
            db.rollback()
            span.set_attribute("db.session.error", True)
            logger.error(f"DB 세션 오류: {e}")
            raise e
        finally:
            db.close()
