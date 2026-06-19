import httpx
from fastapi import HTTPException

from app.schemas.base.auth import KakaoUserInfo

async def get_kakao_access_token(auth_code: str, rest_api_key: str, redirect_uri: str) -> str:
    """인가 코드(Authorization Code)를 사용해 카카오 서버에서 액세스 토큰을 발급받습니다."""
    url = "https://kauth.kakao.com/oauth/token"
    headers = {
        "Content-type": "application/x-www-form-urlencoded;charset=utf-8"
    }
    data = {
        "grant_type": "authorization_code",
        "client_id": rest_api_key,
        "redirect_uri": redirect_uri,
        "code": auth_code
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail={"code": "KAKAO_TOKEN_ISSUE_FAILED", "message": "카카오 액세스 토큰 발급에 실패했습니다."})
            return response.json().get("access_token")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail={"code": "KAKAO_API_CONNECTION_ERROR", "message": f"카카오 API 서버 통신 에러: {str(e)}"})

async def get_kakao_user_info(access_token: str) -> KakaoUserInfo:
    """카카오 서버에 접근하여 액세스 토큰의 유효성을 검증하고 유저 정보를 가져옵니다."""
    url = "https://kapi.kakao.com/v2/user/me"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-type": "application/x-www-form-urlencoded;charset=utf-8"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail={"code": "INVALID_KAKAO_TOKEN", "message": "유효하지 않은 카카오 토큰입니다."})
            return KakaoUserInfo.model_validate(response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail={"code": "KAKAO_API_CONNECTION_ERROR", "message": f"카카오 API 서버 통신 에러: {str(e)}"})