from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from urllib.parse import urlparse
from app.core.config import settings

def create_database_if_not_exists() -> None:
    """데이터베이스가 존재하지 않으면 생성합니다."""
    db_url = settings.DATABASE_URL
    parsed = urlparse(db_url)
    db_name = parsed.path.lstrip('/')
    
    # postgres 데이터베이스에 연결하여 데이터베이스 생성
    postgres_url = db_url.replace(f"/{db_name}", "/postgres")
    
    try:
        # CREATE DATABASE는 트랜잭션 내에서 실행할 수 없으므로 AUTOCOMMIT 모드 적용
        engine = create_engine(postgres_url, isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'"))
            if not result.fetchone():
                print(f"Creating database {db_name}...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"Database {db_name} created!")
            else:
                print(f"Database {db_name} already exists.")
    except Exception as e:
        print(f"Failed to create database: {e}")

def run_migrations() -> None:
    """애플리케이션 시작 시 Alembic 마이그레이션을 자동으로 실행합니다."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    try:
        print("Running DB migrations...")
        command.upgrade(alembic_cfg, "head")
        print("Migrations complete!")
    except Exception as e:
        print(f"Migration failed: {e}")
