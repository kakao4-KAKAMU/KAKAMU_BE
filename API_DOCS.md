# KAKAMU_BE API 명세서

현재 프로젝트에 구현된 주요 API 경로와 설명입니다.  
상세한 API 요청/응답 스키마와 테스트는 서버 실행 후 **Swagger UI (`/docs` 또는 `/api/docs`)**를 통해 확인할 수 있습니다.

## 1. System (시스템 상태 및 연결 확인)
| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | 서버 및 쿠버네티스 헬스 체크 |
| `GET` | `/` | 서버 Root 환영 메시지 |
| `GET` | `/db-test` | PostgreSQL 데이터베이스 연결 상태 테스트 |
| `GET` | `/redis-test` | Redis 연결 및 읽기/쓰기 테스트 |

## 2. Local Auth (일반 계정 인증)
| Method | Path | Description |
|---|---|---|
| `POST` | `/local-auth/login` | 이메일과 비밀번호를 사용하여 일반 로그인 (JWT 발급) |

## 3. Social Auth (소셜 계정 인증)
| Method | Path | Description |
|---|---|---|
| `POST` | `/social-auth/login` | 인가 코드(code) 또는 액세스 토큰(token)으로 소셜 로그인 처리 |

## 4. Users (사용자 관리 및 회원가입)
| Method | Path | Description |
|---|---|---|
| `POST` | `/users/register/local` | 일반 회원가입 (Firebase 번호 인증 + 이메일/비밀번호) |
| `POST` | `/users/register/social` | 소셜 회원가입 (CI 조합 기반의 계정 통합 및 소셜 연동) |
| `GET` | `/users/me` | JWT 토큰을 기반으로 현재 로그인된 사용자의 정보 조회 |
| `GET` | `/users/{user_id}` | 특정 `user_id`를 가진 사용자 정보 조회 |

## 5. Movies (영화 및 추천 시스템)
| Method | Path | Description |
|---|---|---|
| `POST` | `/movies/{movie_id}/watch` | 선택된 페르소나의 영화 시청 행동을 기록 (취향 업데이트) |
| `GET` | `/movies/recommend` | 현재 활성화된 페르소나의 컨텍스트를 기반으로 맞춤형 영화 추천 |

## 6. Test (개발 및 테스트용)
| Method | Path | Description |
|---|---|---|
| `POST` | `/test/activity` | 페르소나 활동 강제 기록 테스트 (Redis 데이터 갱신) |
| `GET` | `/test/context/{persona_id}` | 특정 페르소나의 실시간 컨텍스트(활동 기록 및 장르 선호도) 조회 |

---

### API Prefix 안내
애플리케이션(FastAPI) 설정 시 `main.py`에 적용된 `root_path` 설정에 따라 위 경로 앞에 특정 Prefix(예: `/api`)가 붙을 수 있습니다.  
* 예: `/users/me` ➔ `http://localhost:8000/api/users/me`