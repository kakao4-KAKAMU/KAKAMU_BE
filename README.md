# 🎥 KAKAMU_BE
KAKAMU 프로젝트의 백엔드 저장소입니다. 본 프로젝트는 FastAPI를 기반으로 하며, 멀티 페르소나 기반 영화 추천 SNS 서비스를 위한 API를 제공합니다.

> 📖 **상세한 API 명세는 [API_DOCS.md](./API_DOCS.md)에서 확인할 수 있습니다.**

# 🛠 Tech Stack
Framework: FastAPI
Database: PostgreSQL (with SQLAlchemy)
Migration: Alembic
Caching: Redis
Container: Docker

# 🚀 Getting Started
## 1. Repository Clone & Path
```bash
git clone <repository-url>
cd KAKAMU_BE
```

## 2. 환경 변수 설정
.env.example 파일을 복사하여 .env 파일을 생성하고, 본인의 로컬 환경에 맞는 값을 입력합니다.
---

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
### API Prefix 안내
애플리케이션(FastAPI) 설정 시 `main.py`에 적용된 `root_path` 설정에 따라 위 경로 앞에 특정 Prefix(예: `/api`)가 붙을 수 있습니다.  
* 예: `/users/me` ➔ `http://localhost:8000/api/users/me`

---

# 🚨 주요 에러 코드 안내 (Error Codes)
API 요청 시 발생할 수 있는 주요 예외 상황과 에러 코드(`code`)입니다. 클라이언트는 이 코드를 기반으로 적절한 예외 처리를 수행할 수 있습니다.

| 분류 | Error Code | HTTP Status | Description (발생 원인) |
|---|---|---|---|
| **가입/인증** | `INVALID_FIREBASE_TOKEN` | 400 | Firebase 인증 토큰이 유효하지 않거나 만료됨 |
| **가입/인증** | `DUPLICATE_EMAIL` | 400 | 이미 가입된 이메일 계정 존재 |
| **가입/인증** | `LOCAL_AUTH_ALREADY_LINKED` | 400 | 해당 본인인증(CI)으로 이미 일반 계정이 연결되어 있음 |
| **가입/인증** | `SOCIAL_AUTH_ALREADY_LINKED` | 400 | 해당 본인인증(CI)으로 이미 동일한 소셜 계정(Provider)이 연결되어 있음 |
| **로그인** | `LOGIN_FAILED` | 401 | 일반 로그인 시 이메일 또는 비밀번호 불일치 |
| **소셜 연동** | `KAKAO_API_KEY_NOT_SET` | 500 | 서버에 카카오 REST API 키가 설정되지 않음 |
| **소셜 연동** | `TOKEN_OR_CODE_REQUIRED` | 400 | 소셜 로그인 요청 시 인가 코드나 액세스 토큰이 누락됨 |
| **소셜 연동** | `UNSUPPORTED_SOCIAL_PROVIDER` | 400 | 지원하지 않는 소셜 로그인 제공자 요청 (예: 카카오 외) |
| **소셜 연동** | `KAKAO_TOKEN_ISSUE_FAILED` | 400 | 카카오 서버로부터 액세스 토큰 발급 실패 |
| **소셜 연동** | `INVALID_KAKAO_TOKEN` | 401 | 유효하지 않은 카카오 액세스 토큰 |
| **시스템** | `USER_NOT_FOUND` | 404 | 요청한 사용자를 찾을 수 없음 |
| **시스템** | `REGISTRATION_FAILED` | 500 | 회원가입 처리 중 예기치 않은 서버 에러 발생 |
| **시스템** | `LOGIN_UNEXPECTED_ERROR` | 500 | 로그인 처리 중 예기치 않은 서버 에러 발생 |