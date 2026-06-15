import httpx
from fastapi import HTTPException, UploadFile

IMAGE_SERVER_UPLOAD_URL = "http://10.2.1.10/upload"
IMAGE_PUBLIC_BASE_URL = "http://210.109.52.56/"  # 실제 이미지 접근 가능한 주소로 변경


async def upload_profile_image(file: UploadFile) -> str:
    try:
        file_bytes = await file.read()

        files = {
            "file": (
                file.filename,
                file_bytes,
                file.content_type or "application/octet-stream"
            )
        }

        data = {
            "image_type": "profile"
        }

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                IMAGE_SERVER_UPLOAD_URL,
                files=files,
                data=data
            )

        response.raise_for_status()

        image_url = response.json().get("image_url")

        if not image_url:
            raise HTTPException(
                status_code=500,
                detail="이미지 서버 응답에 image_url이 없습니다."
            )

        return f"{IMAGE_PUBLIC_BASE_URL}/{image_url}"

    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=500,
            detail=f"이미지 업로드 실패: {str(e)}"
        )