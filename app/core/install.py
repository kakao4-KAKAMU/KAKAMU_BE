import os
import sys
import subprocess

def install_requirements():
    """서버 실행 시 requirements.txt의 패키지를 자동 설치합니다."""
    try:
        # 현재 파일(app/core/install.py)을 기준으로 3단계 상위 폴더(프로젝트 루트) 탐색
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        req_path = os.path.join(base_dir, "requirements.txt")
        
        if os.path.exists(req_path):
            print("Checking and installing packages from requirements.txt...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-r", req_path])
    except Exception as e:
        print(f"Failed to install requirements: {e}")