import os
import sys
from logging.config import fileConfig

from app.core.config import settings  # DB URL을 가져오기 위함
from app.db.base import Base          # SQLAlchemy Base 클래스
from app.models.models import *      # 모든 모델을 메모리에 로드하여 감지 가능하게 함

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# -------------------------------------------------------------------------
# 1. 프로젝트 루트 경로 추가 (app 패키지 임포트를 위해 필수)
# -------------------------------------------------------------------------
# 현재 alembic 폴더의 상위 폴더(KAKAMU_BE)를 sys.path에 추가합니다.
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))

# -------------------------------------------------------------------------
# 2. Alembic 설정 객체 및 로깅
# -------------------------------------------------------------------------
# Alembic 설정 객체 (alembic.ini의 값들을 참조함)
config = context.config

# 로깅 설정 적용
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# -------------------------------------------------------------------------
# 3. 핵심 설정: 메타데이터 및 DB URL 동적 지정
# -------------------------------------------------------------------------
# 모델의 변경 사항을 감지하기 위한 메타데이터 지정
target_metadata = Base.metadata

# alembic.ini의 sqlalchemy.url 대신 환경 변수(settings.DATABASE_URL)를 사용하도록 설정
config.set_main_option("sqlalchemy.url", settings.get_database_url())


def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행
    DB에 직접 연결하지 않고 SQL 스크립트만 생성할 때 사용됩니다.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행
    실제 DB에 접속하여 마이그레이션을 수행합니다.
    """
    # config에 설정된 정보를 바탕으로 엔진 생성
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"client_encoding": "utf8"}
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()