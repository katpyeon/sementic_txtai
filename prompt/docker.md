다음 조건을 만족하는 Docker 환경 구성 파일(Dockerfile, docker-compose.yml)을 생성해줘.

### 전제 조건
- 도커는 이미 설치되어 있음
- 파이썬 버전은 3.12 사용
- 기본 빌드도구 설치 (gcc, g++)
- 현재 디렉토리에는 다음 파일이 존재함:
  1. scraper_kyobo.py : 교보문고 리뷰 데이터를 책 코드로 수집하여 CSV로 저장
  2. sentiment_analysis_txtai.py : 감성 분석 및 리포트 생성 스크립트. 옵션:
     -t 책제목
     -f 리뷰 데이터 CSV 경로
  3. requirements.txt : 위 스크립트 실행에 필요한 파이썬 라이브러리 목록

### 기대 동작
- "도서코드 S000212321676 리뷰 분석해줘" 라고 입력하면,
- 도커 컨테이너에서 scraper_kyobo.py 를 실행해 리뷰 데이터 수집 후 `data/` 디렉토리로 이동
- 이어서 sentiment_analysis_txtai.py 를 실행해 `output/` 디렉토리에 리포트 HTML 생성

### Dockerfile 구성
```dockerfile
FROM python:3.12-slim

# 필요한 빌드 도구 설치 (wordcloud 등 컴파일 필요한 패키지를 위해)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# 작업 디렉토리 생성
RUN mkdir -p /app/data /app/output
```

### docker-compose.yml 구성
```yaml
services:
  review-analyzer:
    build: .
    volumes:
      - .:/app  # 전체 프로젝트 디렉토리를 마운트하여 파일 접근성 보장
    environment:
      - PYTHONUNBUFFERED=1  # 파이썬 출력 버퍼링 비활성화
    stdin_open: true  # docker run -i 와 동일
    tty: true        # docker run -t 와 동일
```

### 실행 방법
1. 리뷰 데이터 수집 및 이동:
```bash
# 리뷰 수집 후 data 디렉토리로 이동
docker-compose run --rm review-analyzer /bin/bash -c "\
  python scraper_kyobo.py review S000212321676 && \
  mv 교보_*_리뷰_*.csv data/도서제목_reviews.csv"
```

2. 감성 분석 및 리포트 생성:
```bash
docker-compose run --rm review-analyzer python sentiment_analysis_txtai.py -t "도서제목" -f "data/도서제목_reviews.csv"
```

### 주의사항
1. data/ 와 output/ 디렉토리는 Dockerfile에서 자동 생성
2. 전체 프로젝트 디렉토리를 마운트하여 파일 접근성 문제 해결
3. gcc, g++ 설치로 wordcloud 등 컴파일 필요한 패키지 설치 가능
4. PYTHONUNBUFFERED=1 설정으로 실시간 로그 확인 가능
5. 리뷰 데이터는 먼저 루트에 저장된 후 data/ 디렉토리로 이동됨

### 트러블슈팅
1. "No such file or directory" 에러 발생 시:
   - 컨테이너와 호스트 간 파일 경로가 일치하는지 확인
   - data/ 또는 output/ 디렉토리가 존재하는지 확인
   - 파일 이동 명령어가 정상적으로 실행되었는지 확인

2. 패키지 설치 실패 시:
   - Dockerfile의 빌드 도구 설치 부분 확인
   - requirements.txt의 패키지 버전 호환성 확인

3. 실행 권한 문제 발생 시:
   - 호스트의 data/ 및 output/ 디렉토리 권한 확인
   - 필요시 chmod 명령으로 권한 조정

4. 파일 이동 실패 시:
   - 와일드카드(*) 패턴이 올바른지 확인
   - 이동할 파일이 실제로 존재하는지 확인
   - 대상 디렉토리의 쓰기 권한 확인