# 1. 베이스 이미지 선택
FROM python:3.9-slim

# 2. 작업 디렉터리 설정
WORKDIR /app

# 3. 시스템 의존성 설치
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 4. 파이썬 종속 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 소스 코드 복사
COPY . .

# 6. FastAPI/uvicorn 서버 실행 (포트 8001)
EXPOSE 8001
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]