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
    if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$', v):
        raise ValueError("비밀번호는 영문, 숫자를 포함해야 합니다.")
    return v

NotEmptyStr = Annotated[str, AfterValidator(check_not_empty_str)]
OptionalNotEmptyStr = Annotated[Optional[str], AfterValidator(check_optional_not_empty_str)]
PasswordStr = Annotated[str, AfterValidator(check_password_complexity)]