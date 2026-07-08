import os
import firebase_admin
from firebase_admin import credentials, auth

# firebase-adminsdk.json 파일 경로
# 실제 서비스 시 환경 변수로 관리하거나 안전한 경로에 배치해야 합니다.
# 환경 변수로 적용, 기본 경로 수정 필요
cred_path = os.getenv("FIREBASE_CONFIG_PATH", "./firebase-adminsdk.json")

if os.path.exists(cred_path):
    cred = credentials.Certificate(cred_path)
    # FastAPI의 Hot Reload 상황에서 중복 초기화를 방지합니다.
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
else:
    print(f"Warning: {cred_path} 파일이 존재하지 않습니다. Firebase Auth 토큰 검증이 실패할 수 있습니다.")

def verify_firebase_token(id_token: str) -> str | None:
    """
    Firebase 프론트엔드에서 넘어온 id_token을 검증하고, 
    유효하면 전화번호를 반환합니다.
    """
    # if id_token == "test_code":
    #     return "+821012345678"

    try:


        decoded_token = auth.verify_id_token(id_token)
        phone_number = decoded_token.get('phone_number')
        return phone_number
    except Exception as e:
        print(f"Firebase Token Verification Error: {e}")
        return None
