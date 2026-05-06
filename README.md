# 🎥 KAKAMU_BE
KAKAMU 프로젝트의 백엔드 저장소입니다. 본 프로젝트는 FastAPI를 기반으로 하며, 멀티 페르소나 기반 영화 추천 SNS 서비스를 위한 API를 제공합니다.


# 🛠 Tech Stack
Framework: FastAPI

Database: PostgreSQL (with SQLAlchemy)

Migration: Alembic

Caching: Redis

Container: Docker

# 🚀 Getting Started
## 1. Repository Clone & Path
```
git clone <repository-url>
cd KAKAMU_BE
```

## 2. 환경 변수 설정
.env.example 파일을 복사하여 .env 파일을 생성하고, 본인의 로컬 환경에 맞는 값을 입력합니다.

주의: .env 파일은 한 번 설정된 후 git 추적에서 제외되도록 관리되므로, 변경 사항이 생길 경우 팀 내 공유가 필요합니다.

Bash
cp .env.example .env
## 3. 가상 환경 구축 및 패키지 설치
```
# 가상환경 생성 (Python 3.10+ 권장)
python -m venv venv

# 가상환경 활성화
## Windows:
source venv/Scripts/activate
## Mac/Linux:
source venv/bin/activate

## 패키지 설치
pip install -r requirements.txt
```
## 4. 데이터베이스 마이그레이션
최신 DB 스키마를 반영하기 위해 Alembic을 실행합니다.
```
alembic upgrade head
```
## 5. 서버 실행
```
uvicorn app.main:app --reload
```
서버 실행 후 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)에서 Swagger UI를 확인할 수 있습니다.