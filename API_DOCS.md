# KAKAMU_BE API 명세서

현재 프로젝트에 구현된 주요 API 경로와 설명입니다.  
상세한 API 요청/응답 스키마와 테스트는 서버 실행 후 **Swagger UI (`/docs` 또는 `/api/docs`)**를 통해 확인할 수 있습니다.

## 🔐 API 인증 및 공통 헤더 안내
본 프로젝트는 **상태 비저장(Stateless)** 아키텍처를 채택하고 있습니다. **활동(글쓰기, 팔로우, 좋아요 등)의 주체는 '유저(User)'**이며, **추천 및 알고리즘의 주체는 '페르소나(Persona)'**입니다. 따라서 이 두 가지가 모두 필요한 대부분의 커뮤니티 API는 다음 두 가지를 요청 헤더(Header)에 포함해야 합니다.

1. **Authorization**: `Bearer <Access_Token>` (유저 본인 인증)
2. **X-Persona-Id**: `<현재 활성화된 페르소나의 UUID>` (ML/추천 알고리즘용 컨텍스트)

*💡 프론트엔드는 로그인 후 `/personas` API를 통해 페르소나 목록을 조회하고, 유저가 사용할 페르소나를 선택하면 해당 ID를 로컬 환경에 저장해 두었다가 매 API 호출 시 전송해야 합니다.*

---

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
| `POST` | `/users/me/restore` | 삭제된 회원(유예 기간) 복구 (계정 활성화) |

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
| `GET` | `/posts/{post_id}/comments` | 특정 게시물의 댓글 목록 조회 (Offset 기반 페이징 - `page`, `size` 쿼리 파라미터 지원) |
| `POST` | `/posts/{post_id}/comments` | 특정 게시물에 댓글 및 대댓글 작성 |

## 5. Comments & Likes (단일 댓글 관리 및 좋아요)
| Method | Path | Description |
|---|---|---|
| `GET` | `/comments/{comment_id}` | 단일 댓글 상세 조회 (스포일러 원본 확인용) |
| `PUT` | `/comments/{comment_id}` | 단일 댓글 내용 및 스포일러 여부 수정 (작성자 본인만 가능) |
| `DELETE` | `/comments/{comment_id}` | 단일 댓글 삭제 (Soft Delete, 하위 대댓글 함께 비활성화) |
| `POST` | `/likes` | 대상(게시물/댓글 등)에 대한 좋아요 토글 및 활동 기록 |

## 6. Relations (팔로우 및 차단)
| Method | Path | Description |
|---|---|---|
| `POST` | `/relations/follows/{following_user_id}` | 특정 유저 팔로우 |
| `DELETE` | `/relations/follows/{following_user_id}` | 특정 유저 팔로우 해제 |
| `POST` | `/relations/blocks/{blocked_user_id}` | 특정 유저 차단 |
| `DELETE` | `/relations/blocks/{blocked_user_id}` | 특정 유저 차단 해제 |
| `GET` | `/relations/users/{target_user_id}/followers` | 특정 유저의 팔로워 목록 조회 (무한 스크롤) |
| `GET` | `/relations/users/{target_user_id}/followings` | 특정 유저의 팔로잉 목록 조회 (무한 스크롤) |

## 8. Search (통합 탐색 및 메타데이터)
| Method | Path | Description |
|---|---|---|
| `GET` | `/v1/search/for-you` | 통합 검색 - 추천(For You) 탭 게시물 (취향+정확도+인기도 기반 재정렬) |
| `GET` | `/v1/search/live` | 통합 검색 - 실시간(Live) 탭 게시물 (커서 기반 무한 스크롤, 최신순) |
| `GET` | `/v1/search/user` | 통합 검색 - 유저 탭 유저 목록 (본명 은닉, 복합 커서 기반 무한 스크롤) |
| `GET` | `/v1/search/content` | 통합 검색 - 영화 정보 탭 (영화 메타데이터 검색, 정렬 및 무한 스크롤) |
| `GET` | `/v1/search/movie` | 영화 상세 필터 검색 (이름, 연도, 장르 필터 및 정렬, Offset 페이징) |
| `GET` | `/v1/search/person` | 인물(배우/감독) 검색 (직업 필터, 이름 정렬, Offset 페이징) |
| `GET` | `/v1/genre/list` | 전체 영화 장르 목록 가나다순 조회 |
| `GET` | `/v1/search/trend` | 일간 인기 검색어(트렌드) Top 10 순위 조회 |

## 9. Personas (페르소나 관리)
| Method | Path | Description |
|---|---|---|
| `GET` | `/personas` | 현재 로그인된 유저의 모든 페르소나 목록 조회 |
| `POST` | `/personas` | 신규 페르소나 생성 (최대 5개 제한, 고유 태그 발급) |
| `GET` | `/personas/{persona_id}` | 특정 페르소나 상세 정보 조회 |
| `PUT` | `/personas/{persona_id}` | 특정 페르소나 정보(닉네임, 프로필 이미지, 취향 정보 등) 수정 |
| `DELETE` | `/personas/{persona_id}` | 특정 페르소나 삭제 (Soft Delete, 최소 1개 유지) |

## 10. Static Files (정적 파일 제공)
| Method | Path | Description |
|---|---|---|
| `GET` | `/static/*` | 서버에 저장된 정적 파일(이미지 등) 서빙 |

---
## 11. AI & Chatbot (VLLM 연동)
| Method | Path | Description |
|---|---|---|
| `POST` | `/chat/completions` | VLLM 서버와 통신하여 챗봇 응답 생성 (이전 대화 내역 전달 가능) |

## 12. Activity Logging (사용자 행동 로그)
| Method | Path | Description |
|---|---|---|
| `POST` | `/logs/activity` | 프론트엔드에서 수집한 유저 행동(클릭, 호버 등) 로그를 비동기 큐에 적재 |
---

### API Prefix 안내
애플리케이션(FastAPI) 설정 시 `main.py`에 적용된 `root_path` 설정에 따라 위 경로 앞에 특정 Prefix(예: `/api`)가 붙을 수 있습니다.  
* 예: `/users/me` ➔ `http://localhost:8000/api/users/me`

---

## 🚨 주요 에러 코드 안내 (Error Codes)
본 프로젝트의 에러 코드 명세는 단일 진실 공급원(SSOT) 유지를 위해 별도의 문서로 분리되었습니다.
API 호출 시 발생할 수 있는 주요 예외 상황과 커스텀 에러 코드(`code`), HTTP 상태 코드 및 발생 원인은 **ERROR_CODES.md**를 참조해 주시기 바랍니다.