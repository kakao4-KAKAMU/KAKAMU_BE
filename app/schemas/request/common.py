from typing import Annotated, Optional
from pydantic import AfterValidator
import re

def check_not_empty_str(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("공백으로만 이루어질 수 없습니다.")
    return v

def check_optional_not_empty_str(v: Optional[str]) -> Optional[str]:
    if v is not None:
        v = v.strip()
        if not v:
            raise ValueError("공백으로만 이루어질 수 없습니다.")
    return v

def check_password_complexity(v: str) -> str:
    errors = []
    if len(v) < 8:
        errors.append("8자 이상")
    if not re.search(r"[a-zA-Z]", v):
        errors.append("영문")
    if not re.search(r"\d", v):
        errors.append("숫자")
    
    if errors:
        raise ValueError(f"비밀번호는 다음 조건을 만족해야 합니다: {', '.join(errors)} 포함")
    return v

NotEmptyStr = Annotated[str, AfterValidator(check_not_empty_str)]
OptionalNotEmptyStr = Annotated[Optional[str], AfterValidator(check_optional_not_empty_str)]
PasswordStr = Annotated[str, AfterValidator(check_password_complexity)]