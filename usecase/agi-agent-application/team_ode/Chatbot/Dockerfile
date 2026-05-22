FROM python:3.11-slim

# 필수 패키지 설치 (예: gcc, build-essential은 필요시 추가)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# requirements 먼저 복사해서 Docker 캐시 활용
COPY requirements.txt .

# 필요 패키지 설치
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 앱 소스 전체 복사
COPY . .

# Streamlit 포트 오픈
EXPOSE 8000

# Streamlit 실행
CMD ["python", "main.py"]