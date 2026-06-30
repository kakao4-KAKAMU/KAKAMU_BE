from typing import Literal, Optional, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SaveToggleRequest(BaseModel):
    target_type: Literal["POST", "COMMENT", "MOVIE"] = Field(..., description="POST, COMMENT 또는 MOVIE")
    target_id: Optional[int] = Field(default=None, description="POST/COMMENT ID")
    movie_id: Optional[UUID] = Field(default=None, description="MOVIE ID")

    @model_validator(mode="after")
    def validate_target(self) -> Self:
        if self.target_type in ("POST", "COMMENT"):
            if self.target_id is None:
                raise ValueError("POST/COMMENT 타입은 target_id가 필요합니다.")
            if self.movie_id is not None:
                raise ValueError("POST/COMMENT 타입에는 movie_id를 설정할 수 없습니다.")
        elif self.target_type == "MOVIE":
            if self.movie_id is None:
                raise ValueError("MOVIE 타입은 movie_id가 필요합니다.")
            if self.target_id is not None:
                raise ValueError("MOVIE 타입에는 target_id를 설정할 수 없습니다.")
        return self
