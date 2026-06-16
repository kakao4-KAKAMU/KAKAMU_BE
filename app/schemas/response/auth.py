from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    is_new_user: bool = False

class SocialAuthStatus(BaseModel):
    provider: str
    is_linked: bool
    connected_at: Optional[datetime] = None
    email: Optional[str] = None

class LocalAuthStatus(BaseModel):
    is_linked: bool
    email: Optional[str] = None

class AccountSettingsResponse(BaseModel):
    primary_provider: str
    local_auth: LocalAuthStatus
    social_auths: List[SocialAuthStatus]