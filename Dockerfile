# Dockerfile
FROM python:3.12-slim

# 필요한 빌드 도구 설치 (wordcloud 등 컴파일 필요한 패키지를 위해)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 작업 디렉토리 생성
RUN mkdir -p /app/data /app/output

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["bash"]