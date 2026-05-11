# app/core/config.py[cite: 2, 3]
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "KAKAMU_BE"
    
    # Optional로 변경하여 값이 없을 때 에러가 나는 것을 방지합니다.
    DATABASE_URL: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    POSTGRES_USER: str = Field(default="admin", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(default="password", env="POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = Field(default="db", env="POSTGRES_SERVER")
    POSTGRES_PORT: str = Field(default="5432", env="POSTGRES_PORT")
    POSTGRES_DB: str = Field(default="main_db", env="POSTGRES_DB")
    
    REDIS_URL: str
    
    # JWT Settings
    SECRET_KEY: str = Field(default="supersecretkey_change_in_production", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    def get_database_url(self) -> str:
        # 주입된 URL이 있으면 그것을 반환하고, 없으면 생성합니다. (단, 템플릿 변수가 포함된 경우 제외)
        if self.DATABASE_URL and "${" not in self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        # .env 파일을 읽어오도록 설정합니다. 파일이 프로젝트 루트에 있어야 합니다.
        env_file = ".env"
        case_sensitive = True
        extra = "ignore" # 정의되지 않은 추가 환경 변수는 무시합니다.

settings = Settings()
