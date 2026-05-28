from .auth import get_current_user
from .persona import get_current_persona
from .validation import validate_local_registration, validate_social_registration

def optional_verify_persona_ownership(): # 더미 함수
    """임시 가짜 함수: 검증 없이 Pass"""
    return None

def verify_persona_ownership(): # 더미 함수
    """임시 가짜 함수: 검증 없이 Pass"""
    return None