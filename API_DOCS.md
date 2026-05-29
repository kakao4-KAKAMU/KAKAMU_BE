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

## 2. Users & Auth (회원가입 및 로그인 통합)
| Method | Path | Description |
|---|---|---|
| `POST` | `/users/register/local` | 일반 회원가입 (Firebase 번호 인증 + 이메일/비밀번호) |
| `POST` | `/users/register/social` | 소셜 회원가입 (CI 조합 기반의 계정 통합 및 소셜 연동) |
| `POST` | `/users/login/local` | 이메일과 비밀번호를 사용하여 일반 로그인 (JWT 발급) |
| `POST` | `/users/login/social` | 인가 코드(code) 또는 액세스 토큰(token)으로 소셜 로그인 처리 |
| `POST` | `/users/login/refresh` | 만료된 액세스 토큰 재발급 (리프레시 토큰 검증) |
| `GET` | `/users/me` | JWT 토큰을 기반으로 현재 로그인된 사용자의 정보 조회 |
| `GET` | `/users/{user_id}` | 특정 `user_id`를 가진 사용자 정보 조회 |
| `POST` | `/users/local/reset-password` | Firebase 인증 기반 이메일 계정 비밀번호 재설정 |

## 3. Movies (영화 및 추천 시스템)
| Method | Path | Description |
|---|---|---|
| `POST` | `/movies/{movie_id}/watch` | 선택된 페르소나의 영화 시청 행동을 기록 (취향 업데이트) |
| `GET` | `/movies/recommend` | 현재 활성화된 페르소나의 컨텍스트를 기반으로 맞춤형 영화 추천 |

## 4. Posts (게시물 관리)
| Method | Path | Description |
|---|---|---|
| `GET` | `/posts` | 게시물 피드 조회 (무한 스크롤, `cursor` 기반, 스포일러 마스킹) |
| `GET` | `/posts/liked` | 내가 좋아요를 누른 게시물 목록 조회 (무한 스크롤) |
| `POST` | `/posts` | 새 게시물 작성 (해시태그/멘션 파싱 및 영화 추천 가중치 반영) |
| `GET` | `/posts/{post_id}` | 특정 게시물 상세 조회 (스포일러 마스킹 해제) |
| `PUT` | `/posts/{post_id}` | 게시물 수정 (작성자 본인만 가능) |
| `DELETE` | `/posts/{post_id}` | 게시물 삭제 (Soft Delete, **하위 댓글도 모두 비활성화 처리**) |
| `GET` | `/posts/{post_id}/comments` | 특정 게시물의 댓글 목록 조회 |
| `POST` | `/posts/{post_id}/comments` | 특정 게시물에 댓글 및 대댓글 작성 |

## 5. Comments & Likes (단일 댓글 관리 및 좋아요)
| Method | Path | Description |
|---|---|---|
| `GET` | `/comments/{comment_id}` | 단일 댓글 상세 조회 (스포일러 원본 확인용) |
| `DELETE` | `/comments/{comment_id}` | 단일 댓글 삭제 (Soft Delete, 하위 대댓글 함께 비활성화) |
| `POST` | `/likes` | 대상(게시물/댓글 등)에 대한 좋아요 토글 및 활동 기록 |

## 6. Relations (팔로우 및 차단)
| Method | Path | Description |
|---|---|---|
| `POST` | `/relations/follows/{following_id}` | 특정 페르소나 팔로우 |
| `DELETE` | `/relations/follows/{following_id}` | 특정 페르소나 팔로우 해제 |
| `POST` | `/relations/blocks/{blocked_id}` | 특정 페르소나 차단 (레벨: PERSONA/USER 설정 가능) |
| `DELETE` | `/relations/blocks/{blocked_id}` | 특정 페르소나 차단 해제 |
| `GET` | `/relations/{target_persona_id}/followers` | 특정 페르소나의 팔로워 목록 조회 (무한 스크롤) |
| `GET` | `/relations/{target_persona_id}/followings` | 특정 페르소나의 팔로잉 목록 조회 (무한 스크롤) |

## 7. Test (개발 및 테스트용)
| Method | Path | Description |
|---|---|---|
| `POST` | `/test/activity` | 페르소나 활동 강제 기록 테스트 (Redis 데이터 갱신) |
| `GET` | `/test/context/{persona_id}` | 특정 페르소나의 실시간 컨텍스트(활동 기록 및 장르 선호도) 조회 |
| `GET` | `/test/test-500` | 에러 핸들링 및 로깅 테스트용 강제 500 에러 발생 |

## 8. Search (통합 탐색 및 메타데이터)
| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/search/for-you` | 통합 검색 - 추천(For You) 탭 게시물 (취향+정확도+인기도 기반 재정렬) |
| `GET` | `/v1/search/live` | 통합 검색 - 실시간(Live) 탭 게시물 (커서 기반 무한 스크롤, 최신순) |
| `GET` | `/v1/search/user` | 통합 검색 - 유저 탭 페르소나 목록 (본명 은닉, 복합 커서 기반 무한 스크롤) |
| `GET` | `/v1/search/content` | 통합 검색 - 영화 정보 탭 (영화 메타데이터 검색, 정렬 및 무한 스크롤) |
| `GET` | `/v1/search/movie` | 영화 상세 필터 검색 (이름, 연도, 장르 필터 및 정렬, Offset 페이징) |
| `GET` | `/v1/search/person` | 인물(배우/감독) 검색 (직업 필터, 이름 정렬, Offset 페이징) |
| `GET` | `/v1/genre/list` | 전체 영화 장르 목록 가나다순 조회 |
| `GET` | `/v1/search/trend` | 일간 인기 검색어(트렌드) Top 10 순위 조회 |

---

### API Prefix 안내
애플리케이션(FastAPI) 설정 시 `main.py`에 적용된 `root_path` 설정에 따라 위 경로 앞에 특정 Prefix(예: `/api`)가 붙을 수 있습니다.  
* 예: `/users/me` ➔ `http://localhost:8000/api/users/me`