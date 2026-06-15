# KAKAMU API 에러 코드 명세서

이 문서는 KAKAMU 백엔드 API 호출 시 발생할 수 있는 커스텀 에러 코드(`code`), HTTP 상태 코드, 그리고 주요 발생 원인을 도메인별로 정리한 명세서입니다. 
프론트엔드 예외 처리(Error Handling) 시 이 문서를 기준으로 `response.data.detail.code`를 확인하여 적절한 UI 메시지를 노출하시기 바랍니다.

## 1. Auth & Users (가입 및 로그인)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `400` | `INVALID_FIREBASE_TOKEN` | Firebase 인증 토큰이 유효하지 않거나 만료됨 |
| `400` | `DUPLICATE_EMAIL` | 이미 가입된 이메일 계정 존재 |
| `400` | `LOCAL_AUTH_ALREADY_LINKED` | 해당 본인인증(CI)으로 이미 일반 계정이 연결되어 있음 |
| `400` | `SOCIAL_AUTH_ALREADY_LINKED` | 해당 본인인증(CI)으로 이미 동일한 소셜 계정(Provider)이 연결되어 있음 |
| `400` | `TOKEN_OR_CODE_REQUIRED` | 소셜 로그인 요청 시 인가 코드나 액세스 토큰이 누락됨 |
| `400` | `UNSUPPORTED_SOCIAL_PROVIDER` | 지원하지 않는 소셜 로그인 제공자 요청 (예: 카카오 외) |
| `400` | `KAKAO_TOKEN_ISSUE_FAILED` | 카카오 서버로부터 액세스 토큰 발급 실패 |
| `401` | `LOGIN_FAILED` | 일반 로그인 시 이메일 또는 비밀번호 불일치 |
| `401` | `INVALID_KAKAO_TOKEN` | 유효하지 않은 카카오 액세스 토큰 |
| `403` | `ACCOUNT_IN_GRACE_PERIOD` | 탈퇴 유예 기간(30일) 내의 계정으로 로그인 시도. 복구 절차 필요 |
| `404` | `USER_NOT_FOUND` | 요청한 사용자를 찾을 수 없음 |
| `400` | `NICKNAME_UNAVAILABLE` | 해당 닉네임은 현재 사용할 수 없음 (회원정보 수정 시 태그 발급 20회 모두 실패) |
| `500` | `KAKAO_API_KEY_NOT_SET` | 서버에 카카오 REST API 키가 설정되지 않음 |
| `500` | `KAKAO_API_CONNECTION_ERROR` | 카카오 API 서버 통신 에러 |
| `500` | `REGISTRATION_FAILED` | 회원가입 처리 중 예기치 않은 서버 에러 발생 |
| `500` | `LOGIN_UNEXPECTED_ERROR` | 로그인 처리 중 예기치 않은 서버 에러 발생 |
| `500` | `USER_UPDATE_FAILED` | 사용자 정보 수정 중 서버(DB) 오류 발생 |
| `500` | `DB_COMMIT_ERROR` | 비밀번호 재설정 등 정보 갱신 중 서버(DB) 오류 발생 |

## 2. Profile (페르소나 관련)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `400` | `MISSING_NICKNAME` | 페르소나 생성 시 닉네임 누락 ("닉네임을 입력해주세요") |
| `400` | `PERSONA_LIMIT_EXCEEDED` | 생성 가능한 최대 페르소나 개수(5개) 초과 |
| `400` | `MINIMUM_PERSONA_REQUIRED` | 최소 1개의 페르소나는 유지해야 하므로 삭제 불가능 |
| `400` | `SAME_NICKNAME` | 닉네임 변경 시 기존과 동일하게 요청함 |
| `403` | `FORBIDDEN_PERSONA_UPDATE` | 본인 소유가 아닌 타인의 페르소나 수정 시도 |
| `404` | `PERSONA_NOT_FOUND` | 존재하지 않거나 삭제된 페르소나 조회/수정 |
| `500` | `TAG_GENERATION_FAILED` | 랜덤 태그(5자리) 중복 및 재생성 로직 실패 |
| `500` | `PERSONA_DELETE_FAILED` | 페르소나 삭제 중 데이터베이스 오류 발생 |
| `500` | `DATABASE_SAVE_FAILED` | 페르소나 생성/수정 시 DB 저장 실패 |

## 3. Comment (댓글 관련)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `404` | `POST_NOT_FOUND` | 삭제된 게시물에 댓글을 작성하려고 시도 |
| `404` | `COMMENT_NOT_FOUND` | 존재하지 않거나 이미 삭제된 댓글 조회/수정/삭제 시도 |
| `403` | `FORBIDDEN_COMMENT_UPDATE` | 본인이 작성하지 않은 댓글을 수정하려고 시도 |
| `403` | `FORBIDDEN_COMMENT_DELETE` | 본인이 작성하지 않은 댓글을 삭제하려고 시도 |
| `403` | `FORBIDDEN_BLOCKED_COMMENT` | 차단 관계에 있는 사용자의 단일 댓글 상세 조회 시도 |

## 4. Post (게시물 관련)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `404` | `POST_NOT_FOUND` | 존재하지 않거나 이미 삭제된 게시물 조회 시도 |
| `403` | `FORBIDDEN_POST_UPDATE` | 본인이 작성하지 않은 게시물 수정 시도 |
| `403` | `FORBIDDEN_POST_DELETE` | 본인이 작성하지 않은 게시물 삭제 시도 |
| `403` | `FORBIDDEN_BLOCKED_POST` | 차단 관계에 있는 사용자의 게시물을 링크로 직접 상세 조회 시도 |
| `400` | `HASHTAG_LIMIT_EXCEEDED` | 본문에 삽입된 해시태그 최대 등록 개수(10개) 초과 |

## 5. Like (좋아요 관련)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `400` | `UNSUPPORTED_TARGET_TYPE` | 좋아요가 불가능한 타겟 타입(게시물, 댓글 외) 요청 |
| `404` | `TARGET_NOT_FOUND` | 좋아요를 누르려는 대상 원본 데이터가 존재하지 않음 |

## 6. Relation (팔로우 및 차단 관련)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `400` | `CANNOT_FOLLOW_SELF` | 본인을 팔로우 대상으로 지정 |
| `400` | `CANNOT_BLOCK_SELF` | 본인을 차단 대상으로 지정 |

## 7. System (시스템 공통)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `500` | `DB_CONNECTION_FAILED` | `/db-test` Health check 중 데이터베이스 연결 실패 |
| `503` | `ML_SERVER_UNAVAILABLE` | 추천 서버(ML/VLLM)와 통신할 수 없거나 응답이 지연됨 |

## 8. Global (공통 API 에러)
| HTTP Status | Error Code | 발생 원인 / 설명 |
|:---:|:---|:---|
| `401` | `UNAUTHORIZED` | JWT 액세스 토큰이 누락되었거나, 만료/유효하지 않은 토큰으로 보호된 API에 접근 시도 |
| `422` | `VALIDATION_ERROR` | 요청 데이터 형식(JSON 바디, 파라미터 등)이 올바르지 않음 (FastAPI 전역 예외 처리) |

---

> 💡 위 에러 코드들은 `app.middleware.logging_middleware.py`에 의해 모두 고유 아이디(`X-Request-ID`)와 함께 로깅됩니다. 원인을 파악하기 힘든 서버 에러(`5xx`)가 발생할 경우 클라이언트에서 받은 `X-Request-ID` 헤더 값을 공유하면 백엔드 서버 로그에서 바로 조회할 수 있습니다.