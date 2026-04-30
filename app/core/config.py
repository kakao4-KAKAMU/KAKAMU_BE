import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # 환경 변수 이름을 컨테이너 설정과 대소문자까지 일치시킵니다.
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str

    # DATABASE_URL을 프로퍼티로 만들어서 호출될 때 환경 변수들이 합쳐지도록 합니다.
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # 환경 변수 우선순위 및 대소문자 설정
    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()
