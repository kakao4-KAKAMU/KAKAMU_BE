# app/core/config.py[cite: 2, 3]
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )
    PROJECT_NAME: str = "KAKAMU_BE"
    # 클라우드 퍼블릭 VM IP
    IMAGE_SERVER_URL: str = "http://210.109.52.56/var/www/images"

    DEFAULT_IMAGE: str = "http://210.109.52.56/api/api"

    # Optional로 변경하여 값이 없을 때 에러가 나는 것을 방지합니다.
    DATABASE_URL: Optional[str] = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )

    POSTGRES_USER: str = Field(
        default="admin",
        validation_alias="POSTGRES_USER",
    )
    POSTGRES_PASSWORD: str = Field(
        default="password",
        validation_alias="POSTGRES_PASSWORD",
    )
    POSTGRES_SERVER: str = Field(
        default="db",
        validation_alias="POSTGRES_SERVER",
    )
    POSTGRES_PORT: str = Field(
        default="5432",
        validation_alias="POSTGRES_PORT",
    )
    POSTGRES_DB: str = Field(
        default="main_db",
        validation_alias="POSTGRES_DB",
    )

    REDIS_URL: str = Field(
        default=None,
        validation_alias="REDIS_URL",
    )

    # JWT Settings
    SECRET_KEY: str = Field(
        default="supersecretkey_change_in_production", validation_alias="SECRET_KEY"
    )
    ALGORITHM: str = Field(default="HS256", validation_alias="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 3, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )  # 3시간 (보안을 위해 짧게 설정)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24 * 14, validation_alias="REFRESH_TOKEN_EXPIRE_MINUTES"
    )  # 14일 (로그인 유지용)

    # Social Auth
    KAKAO_REST_API_KEY: str = Field(default="", validation_alias="KAKAO_REST_API_KEY")

    # ML Server (OpenAPI: http://210.109.52.56/chat-api/openapi.json)
    ML_API_BASE_URL: str = Field(
        default="http://localhost:8080/chat-api", validation_alias="ML_API_BASE_URL"
    )

    def get_database_url(self) -> str:
        # 주입된 URL이 있으면 그것을 반환하고, 없으면 생성합니다. (단, 템플릿 변수가 포함된 경우 제외)
        if self.DATABASE_URL and "${" not in self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
