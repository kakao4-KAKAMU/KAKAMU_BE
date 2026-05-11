# 1. Python 3.11 슬림 이미지 사용
FROM python:3.11-slim

# 2. 필수 시스템 패키지 설치 (PostgreSQL 드라이버 빌드용)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 3. 작업 디렉토리 설정
WORKDIR /app

# 4. 의존성 설치 (캐시 활용을 위해 COPY 순서 최적화)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. 소스 코드 복사
COPY . .

# 6. 환경 변수 기본값 (필요시 빌드 시점에 수정 가능)
ENV PYTHONUNBUFFERED=1

# 7. 실행 명령 (Gunicorn과 Uvicorn 조합으로 운영 성능 확보)
# -w 4: 워커 프로세스 수 (CPU 코어 수에 맞춰 조절)
CMD ["python", "-m" ,"uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]