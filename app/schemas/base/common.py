from typing import Optional

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    status: str = Field(default="success", description="응답 상태")
    message: Optional[str] = Field(default=None, description="성공 메시지 (선택)")


class SuccessMessageResponse(BaseModel):
    message: str = Field(..., description="성공 메시지")
