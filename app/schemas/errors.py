from typing import Any, Dict

def create_error_schema(description: str, code: str, message: str) -> Dict[str, Any]:
    """Swagger 문서에 노출될 에러 응답 스키마를 생성합니다."""
    return {
        "description": description,
        "content": {
            "application/json": {
                "example": {"detail": {"code": code, "message": message}}
            }
        }
    }

# ==========================================
# 1. Auth & Users (가입 및 로그인)
# ==========================================
ERROR_INVALID_FIREBASE_TOKEN = create_error_schema("Firebase 토큰 오류", "INVALID_FIREBASE_TOKEN", "Firebase 인증 토큰이 유효하지 않거나 만료됨")
ERROR_DUPLICATE_EMAIL = create_error_schema("이메일 중복", "DUPLICATE_EMAIL", "이미 가입된 이메일 계정 존재")
ERROR_LOCAL_AUTH_ALREADY_LINKED = create_error_schema("일반 계정 연동됨", "LOCAL_AUTH_ALREADY_LINKED", "해당 본인인증(CI)으로 이미 일반 계정이 연결되어 있음")
ERROR_SOCIAL_AUTH_ALREADY_LINKED = create_error_schema("소셜 계정 연동됨", "SOCIAL_AUTH_ALREADY_LINKED", "해당 본인인증(CI)으로 이미 동일한 소셜 계정이 연결되어 있음")
ERROR_TOKEN_OR_CODE_REQUIRED = create_error_schema("인증 정보 누락", "TOKEN_OR_CODE_REQUIRED", "소셜 로그인 요청 시 인가 코드나 액세스 토큰이 누락됨")
ERROR_UNSUPPORTED_SOCIAL_PROVIDER = create_error_schema("지원하지 않는 소셜", "UNSUPPORTED_SOCIAL_PROVIDER", "지원하지 않는 소셜 로그인 제공자 요청")
ERROR_KAKAO_TOKEN_ISSUE_FAILED = create_error_schema("카카오 토큰 발급 실패", "KAKAO_TOKEN_ISSUE_FAILED", "카카오 서버로부터 액세스 토큰 발급 실패")

ERROR_RESET_PASSWORD_FAILURES = {
    "description": "비밀번호 재설정 실패 (잘못된 요청)",
    "content": {
        "application/json": {
            "examples": {
                "InvalidFirebaseToken": {"summary": "유효하지 않은 토큰", "value": {"detail": {"code": "INVALID_FIREBASE_TOKEN", "message": "유효하지 않거나 만료된 Firebase 토큰입니다."}}},
                "SocialUser": {"summary": "소셜 가입 계정", "value": {"detail": {"code": "SOCIAL_USER", "message": "소셜 로그인으로 가입된 계정입니다. 해당 소셜 서비스를 통해 로그인해주세요."}}}
            }
        }
    }
}

ERROR_LOGIN_FAILED = create_error_schema("로그인 실패", "LOGIN_FAILED", "일반 로그인 시 이메일 또는 비밀번호 불일치")
ERROR_INVALID_KAKAO_TOKEN = create_error_schema("유효하지 않은 카카오 토큰", "INVALID_KAKAO_TOKEN", "유효하지 않은 카카오 액세스 토큰")

ERROR_ACCOUNT_IN_GRACE_PERIOD = create_error_schema("탈퇴 유예 기간", "ACCOUNT_IN_GRACE_PERIOD", "탈퇴 유예 기간(30일) 내의 계정으로 로그인 시도. 복구 절차 필요")

ERROR_USER_NOT_FOUND = create_error_schema("사용자 없음", "USER_NOT_FOUND", "요청한 사용자를 찾을 수 없음")

ERROR_KAKAO_API_KEY_NOT_SET = create_error_schema("카카오 키 미설정", "KAKAO_API_KEY_NOT_SET", "서버에 카카오 REST API 키가 설정되지 않음")
ERROR_KAKAO_API_CONNECTION_ERROR = create_error_schema("카카오 API 통신 에러", "KAKAO_API_CONNECTION_ERROR", "카카오 API 서버 통신 에러")
ERROR_REGISTRATION_FAILED = create_error_schema("회원가입 에러", "REGISTRATION_FAILED", "회원가입 처리 중 예기치 않은 서버 에러 발생")
ERROR_LOGIN_UNEXPECTED_ERROR = create_error_schema("로그인 에러", "LOGIN_UNEXPECTED_ERROR", "로그인 처리 중 예기치 않은 서버 에러 발생")

# ------------------------------------------
# (추가) 다중 에러 묶음 예시 (Refresh Token 401 에러들)
# ------------------------------------------
ERROR_REFRESH_TOKEN_FAILURES = {
    "description": "토큰 갱신 실패 (다양한 원인)",
    "content": {
        "application/json": {
            "examples": {
                "TokenExpired": {"summary": "토큰 만료", "value": {"detail": {"code": "TOKEN_EXPIRED", "message": "리프레시 토큰이 만료되었습니다. 다시 로그인해주세요."}}},
                "InvalidToken": {"summary": "유효하지 않은 토큰", "value": {"detail": {"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다."}}},
                "InvalidType": {"summary": "토큰 타입 오류", "value": {"detail": {"code": "INVALID_TOKEN_TYPE", "message": "리프레시 토큰이 아닙니다."}}},
                "InvalidPayload": {"summary": "페이로드 오류", "value": {"detail": {"code": "INVALID_TOKEN_PAYLOAD", "message": "토큰 내 사용자 정보가 없습니다."}}}
            }
        }
    }
}

ERROR_LOCAL_LINK_FAILURES = {
    "description": "일반 계정 연동 실패 (다양한 원인)",
    "content": {
        "application/json": {
            "examples": {
                "EmailRequired": {"summary": "이메일 누락", "value": {"detail": {"code": "EMAIL_REQUIRED", "message": "소셜 계정에 등록된 이메일이 없습니다. 연동할 이메일을 직접 입력해주세요."}}},
                "LocalAuthAlreadyLinked": {"summary": "일반 계정 이미 연동됨", "value": {"detail": {"code": "LOCAL_AUTH_ALREADY_LINKED", "message": "이미 이메일 로그인 정보가 연동되어 있습니다."}}},
                "DuplicateEmail": {"summary": "이메일 중복", "value": {"detail": {"code": "DUPLICATE_EMAIL", "message": "이미 등록된 이메일입니다."}}}
            }
        }
    }
}

ERROR_SOCIAL_LINK_FAILURES = {
    "description": "소셜 계정 연동 실패 (다양한 원인)",
    "content": {
        "application/json": {
            "examples": {
                "UnsupportedProvider": {"summary": "지원하지 않는 소셜", "value": {"detail": {"code": "UNSUPPORTED_PROVIDER", "message": "지원하지 않는 소셜 플랫폼입니다."}}},
                "SocialAuthAlreadyLinked": {"summary": "소셜 계정 이미 연동됨", "value": {"detail": {"code": "SOCIAL_AUTH_ALREADY_LINKED", "message": "이미 연동된 소셜 계정입니다."}}},
                "SocialAccountAlreadyUsed": {"summary": "다른 사용자가 이미 연동함", "value": {"detail": {"code": "SOCIAL_ACCOUNT_ALREADY_USED", "message": "이 소셜 계정은 이미 다른 사용자와 연동되어 있습니다."}}}
            }
        }
    }
}

ERROR_INVALID_SOCIAL_TOKEN = create_error_schema("유효하지 않은 소셜 토큰", "INVALID_SOCIAL_TOKEN", "유효하지 않은 소셜 토큰입니다.")

# ==========================================
# 2. Profile (페르소나 관련)
# ==========================================
ERROR_MISSING_NICKNAME = create_error_schema("닉네임 누락", "MISSING_NICKNAME", "페르소나 생성 시 닉네임 누락 ('닉네임을 입력해주세요')")
ERROR_PERSONA_LIMIT_EXCEEDED = create_error_schema("페르소나 개수 초과", "PERSONA_LIMIT_EXCEEDED", "생성 가능한 최대 페르소나 개수(5개) 초과")
ERROR_MINIMUM_PERSONA_REQUIRED = create_error_schema("최소 페르소나 유지", "MINIMUM_PERSONA_REQUIRED", "최소 1개의 페르소나는 유지해야 하므로 삭제 불가능")
ERROR_SAME_NICKNAME = create_error_schema("동일한 닉네임", "SAME_NICKNAME", "닉네임 변경 시 기존과 동일하게 요청함")
ERROR_FORBIDDEN_PERSONA_UPDATE = create_error_schema("권한 없음", "FORBIDDEN_PERSONA_UPDATE", "본인 소유가 아닌 타인의 페르소나 수정 시도")
ERROR_PERSONA_NOT_FOUND = create_error_schema("페르소나 없음", "PERSONA_NOT_FOUND", "존재하지 않거나 삭제된 페르소나 조회/수정")
ERROR_TAG_GENERATION_FAILED = create_error_schema("태그 생성 실패", "TAG_GENERATION_FAILED", "랜덤 태그(5자리) 중복 및 재생성 로직 실패")
ERROR_PERSONA_DELETE_FAILED = create_error_schema("페르소나 삭제 에러", "PERSONA_DELETE_FAILED", "페르소나 삭제 중 데이터베이스 오류 발생")
ERROR_DATABASE_SAVE_FAILED = create_error_schema("DB 저장 실패", "DATABASE_SAVE_FAILED", "페르소나 생성/수정 시 DB 저장 실패")

ERROR_CREATE_PERSONA_FAILURES = {
    "description": "페르소나 생성 실패 (다양한 원인)",
    "content": {
        "application/json": {
            "examples": {
                "MissingNickname": {"summary": "닉네임 누락", "value": {"detail": {"code": "MISSING_NICKNAME", "message": "닉네임을 입력해주세요"}}},
                "PersonaLimitExceeded": {"summary": "개수 초과", "value": {"detail": {"code": "PERSONA_LIMIT_EXCEEDED", "message": "페르소나 계정은 최대 5개 생성 가능합니다."}}}
            }
        }
    }
}

# ==========================================
# 3. Comment (댓글 관련)
# ==========================================
ERROR_POST_NOT_FOUND_FOR_COMMENT = create_error_schema("게시물 없음", "POST_NOT_FOUND", "삭제된 게시물에 댓글을 작성하려고 시도")
ERROR_COMMENT_NOT_FOUND = create_error_schema("댓글 없음", "COMMENT_NOT_FOUND", "존재하지 않거나 이미 삭제된 댓글 조회/수정/삭제 시도")
ERROR_FORBIDDEN_COMMENT_UPDATE = create_error_schema("권한 없음", "FORBIDDEN_COMMENT_UPDATE", "본인이 작성하지 않은 댓글을 수정하려고 시도")
ERROR_FORBIDDEN_COMMENT_DELETE = create_error_schema("권한 없음", "FORBIDDEN_COMMENT_DELETE", "본인이 작성하지 않은 댓글을 삭제하려고 시도")
ERROR_FORBIDDEN_BLOCKED_COMMENT = create_error_schema("권한 없음 (차단 관계)", "FORBIDDEN_BLOCKED_COMMENT", "차단 관계에 있는 사용자의 단일 댓글 상세 조회 시도")

# ==========================================
# 4. Post (게시물 관련)
# ==========================================
ERROR_POST_NOT_FOUND = create_error_schema("게시물 없음", "POST_NOT_FOUND", "존재하지 않거나 이미 삭제된 게시물입니다.")
ERROR_FORBIDDEN_POST_UPDATE = create_error_schema("권한 없음", "FORBIDDEN_POST_UPDATE", "본인이 작성하지 않은 게시물 수정 시도")
ERROR_FORBIDDEN_POST_DELETE = create_error_schema("권한 없음", "FORBIDDEN_POST_DELETE", "본인이 작성하지 않은 게시물 삭제 시도")
ERROR_FORBIDDEN_BLOCKED_POST = create_error_schema("권한 없음 (차단 관계)", "FORBIDDEN_BLOCKED_POST", "차단 관계에 있는 사용자의 게시물을 링크로 직접 상세 조회 시도")
ERROR_HASHTAG_LIMIT_EXCEEDED = create_error_schema("잘못된 요청 (해시태그 초과)", "HASHTAG_LIMIT_EXCEEDED", "본문에 삽입된 해시태그 최대 등록 개수(10개) 초과")

# ==========================================
# 5. Like (좋아요 관련)
# ==========================================
ERROR_UNSUPPORTED_TARGET_TYPE = create_error_schema("지원하지 않는 타겟", "UNSUPPORTED_TARGET_TYPE", "좋아요가 불가능한 타겟 타입(게시물, 댓글 외) 요청")
ERROR_TARGET_NOT_FOUND = create_error_schema("대상 없음", "TARGET_NOT_FOUND", "좋아요를 누르려는 대상 원본 데이터가 존재하지 않음")

# ==========================================
# 6. Relation (팔로우 및 차단 관련)
# ==========================================
ERROR_CANNOT_FOLLOW_SELF = create_error_schema("본인 팔로우 불가", "CANNOT_FOLLOW_SELF", "본인의 페르소나를 팔로우 대상으로 지정")
ERROR_CANNOT_BLOCK_SELF = create_error_schema("본인 차단 불가", "CANNOT_BLOCK_SELF", "본인의 페르소나를 차단 대상으로 지정")

# ==========================================
# 7. System (시스템 공통)
# ==========================================
ERROR_DB_CONNECTION_FAILED = create_error_schema("DB 연결 실패", "DB_CONNECTION_FAILED", "/db-test Health check 중 데이터베이스 연결 실패")

# ==========================================
# 8. Global (공통 API 에러)
# ==========================================
ERROR_VALIDATION_ERROR = create_error_schema("유효성 검사 실패", "VALIDATION_ERROR", "요청 데이터 형식이 올바르지 않습니다.")
ERROR_UNAUTHORIZED = create_error_schema("인증 실패", "UNAUTHORIZED", "인증 토큰이 누락되었거나 유효하지 않은 토큰으로 접근 시도")

# ==========================================
# 9. 기타 누락된 에러 (회원 정보 수정 등)
# ==========================================
ERROR_NICKNAME_UNAVAILABLE = create_error_schema("닉네임 사용 불가", "NICKNAME_UNAVAILABLE", "해당 닉네임은 현재 사용할 수 없습니다. (태그 발급 실패)")
ERROR_USER_UPDATE_FAILED = create_error_schema("회원 정보 수정 실패", "USER_UPDATE_FAILED", "사용자 정보 수정 중 서버 오류 발생")
ERROR_DB_COMMIT_ERROR = create_error_schema("DB 반영 실패", "DB_COMMIT_ERROR", "서버 내부 DB 반영 중 오류 발생")