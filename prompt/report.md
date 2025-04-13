# 도서 정보
도서명: "소년이 온다"
도서코드: S000000610612
CSV파일명: 소년이_온다_reviews.csv
REPORT파일명: 소년이_온다_report.html

# 작업 환경
작업 디렉토리: 현재 프로젝트 루트  
도커 컴포즈 서비스명: review-analyzer

# 작업 순서
1. scraper_kyobo.py 를 실행하여 도서코드에 해당하는 리뷰 데이터를 수집하여 data/ 디렉토리에 저장
   → 명령어:
   ```bash
   docker-compose run --rm review-analyzer /bin/bash -c "\
     python scraper_kyobo.py review ${도서코드} && \
     mv 교보_${도서코드}_리뷰_*.csv data/${CSV파일명}"
   ```

2. sentiment_analysis_txtai.py 를 실행하여 감정 분석 후 output/ 디렉토리에 리포트 생성
   → 명령어:
   ```bash
   docker-compose run --rm review-analyzer python sentiment_analysis_txtai.py \
     -t "${도서명}" \
     -f "data/${CSV파일명}" \
     -o "output/${REPORT파일명}"
   ```

# 결과물
- 리뷰 데이터 CSV: `data/${CSV파일명}`
- 분석 리포트 HTML: `output/${REPORT파일명}`
