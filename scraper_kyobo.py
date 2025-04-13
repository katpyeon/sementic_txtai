import requests
import json
import csv
import os
from datetime import datetime
import pandas as pd

def scrap_category_book_list(sale_cmdt_clst_code, output_path=None):
    """
    교보문고 카테고리별 도서 목록을 스크랩하여 CSV 파일로 저장합니다.
    
    Args:
        sale_cmdt_clst_code (str): 교보문고 카테고리 코드
        output_path (str, optional): 출력 파일 경로. 지정하지 않으면 현재 디렉토리에 생성됩니다.
    
    Returns:
        str: 처리 결과 메시지
    """
    # 기본 URL과 헤더 설정
    base_url = 'https://product.kyobobook.co.kr/api/gw/pdt/category/all'
    headers = {
        'authority': 'product.kyobobook.co.kr',
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9',
        'cache-control': 'no-cache',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    page = 1
    all_data = []
    
    # 데이터 수집
    while True:
        params = {
            'page': page,
            'per': 100,
            'saleCmdtDvsnCode': 'KOR',
            'saleCmdtClstCode': sale_cmdt_clst_code,
            'isEvent': False,
            'isPackage': False,
            'isMDPicked': False,
            'sort': 'new'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            data = response.json()
            
            # 현재 페이지 데이터 추출
            current_data = data['data']['tabContents']
            
            # 데이터가 없으면 종료
            if not current_data or len(current_data) == 0:
                break
                
            # 데이터 누적
            all_data.extend(current_data)
            
            # 전체 데이터 수 도달 시 종료
            if len(all_data) >= data['data']['totalCount']:
                break
                
            page += 1
            
        except Exception as e:
            print(f'오류 발생: {str(e)}')
            break
    
    # 데이터가 있는 경우 CSV 파일로 출력
    if all_data:
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"카테고리{sale_cmdt_clst_code}_도서목록_{timestamp}.csv"
        
        if output_path:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            filepath = os.path.join(output_path, filename)
        else:
            filepath = filename
        
        # CSV 파일로 저장
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # 컬럼 정의
            fieldnames = [
                '상품ID', '상품명', '상품코드', '상품그룹구분코드', '상품구분코드',
                '상품분류코드', '출판사명', '출시일', '내용소개', '가격',
                '상품상태코드', '배송구분코드', '전체리뷰내용', '리뷰평균평점',
                '베스트키워드명', '상품분류명', '문화공간', '기간', '전시상품구분코드',
                '좋아요', '장바구니', '구매', '직접구매', '상세보기',
                '스티키', '재입고여부', '출시여부', '배송코드', '배송텍스트',
                '배송종류', '오늘의책', '오늘의책라벨', 'MD추천', '특별주문',
                '교보전용', '한정판매', '사은품', '이벤트', '소득공제',
                '고정가격', '제본', '할인가격'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # 데이터 가공 및 저장
            for item in all_data:
                product_info = item.get('productInfo', {})
                row = {
                    '상품ID': item.get('saleCmdtId', ''),
                    '상품명': item.get('cmdtName', ''),
                    '상품코드': item.get('cmdtcode', ''),
                    '상품그룹구분코드': item.get('saleCmdtGrpDvsnCode', ''),
                    '상품구분코드': item.get('saleCmdtDvsnCode', ''),
                    '상품분류코드': item.get('saleCmdtClstCode', ''),
                    '출판사명': item.get('pbcmName', ''),
                    '출시일': item.get('rlseDate', ''),
                    '내용소개': item.get('inbukCntt', ''),
                    '가격': item.get('price', ''),
                    '상품상태코드': item.get('cmdtCdtnCode', ''),
                    '배송구분코드': item.get('bkbnShpCode', ''),
                    '전체리뷰내용': item.get('whlRevwCont', ''),
                    '리뷰평균평점': item.get('revwRvgrAvg', ''),
                    '베스트키워드명': item.get('bestEmtnKywrName', ''),
                    '상품분류명': item.get('saleCmdtClstName', ''),
                    '문화공간': item.get('clturPlce', ''),
                    '기간': item.get('period', ''),
                    '전시상품구분코드': item.get('enbsCmdtDvsnCode', ''),
                    '좋아요': product_info.get('like', ''),
                    '장바구니': product_info.get('basket', ''),
                    '구매': product_info.get('buy', ''),
                    '직접구매': product_info.get('direct', ''),
                    '상세보기': product_info.get('viewDetails', ''),
                    '스티키': product_info.get('sticky', ''),
                    '재입고여부': product_info.get('reStockOnOff', ''),
                    '출시여부': product_info.get('releaseOnOff', ''),
                    '배송코드': product_info.get('shippingCode', ''),
                    '배송텍스트': product_info.get('shippingText', ''),
                    '배송종류': product_info.get('shippingKind', ''),
                    '오늘의책': product_info.get('todayBook', ''),
                    '오늘의책라벨': product_info.get('todayBookLabel', ''),
                    'MD추천': product_info.get('mdChoice', ''),
                    '특별주문': product_info.get('specialOrder', ''),
                    '교보전용': product_info.get('onlyKyobo', ''),
                    '한정판매': product_info.get('limitSale', ''),
                    '사은품': product_info.get('gifts', ''),
                    '이벤트': product_info.get('event', ''),
                    '소득공제': product_info.get('incomeDeduction', ''),
                    '고정가격': product_info.get('fixPrice', ''),
                    '제본': product_info.get('bind', ''),
                    '할인가격': product_info.get('cutPrice', '')
                }
                writer.writerow(row)
        
        return f"총 {len(all_data)}개의 도서 정보가 '{filepath}' 파일에 저장되었습니다."
    else:
        return "데이터 수집에 실패했습니다."

def scrap_review(book_code, output_path=None):
    """
    교보문고 도서 리뷰를 스크랩하여 CSV 파일로 저장합니다.
    
    Args:
        book_code (str): 교보문고 상품 코드
        output_path (str, optional): 출력 파일 경로. 지정하지 않으면 현재 디렉토리에 생성됩니다.
    
    Returns:
        str: 처리 결과 메시지
    """
    base_url = 'https://product.kyobobook.co.kr/api/review/list'
    headers = {
        'authority': 'product.kyobobook.co.kr',
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': f'https://product.kyobobook.co.kr/detail/{book_code}',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    }
    
    page = 1
    all_data = []
    
    # 데이터 수집
    while True:
        params = {
            'page': page,
            'pageLimit': 100,
            'reviewSort': '001',
            'revwPatrCode': '002',
            'saleCmdtid': book_code
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            data = response.json()
            
            # 리뷰 목록 추출
            reviews = data['data']['reviewList']
            
            # 데이터가 없으면 종료
            if not reviews or len(reviews) == 0:
                break
                
            # 데이터 누적
            all_data.extend(reviews)
            page += 1
            
        except Exception as e:
            print(f'오류 발생: {str(e)}')
            break
    
    # 데이터가 있는 경우 CSV 파일로 출력
    if all_data:
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"교보_{book_code}_리뷰_{timestamp}.csv"
        
        if output_path:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            filepath = os.path.join(output_path, filename)
        else:
            filepath = filename
        
        # CSV 파일로 저장
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['리뷰번호', '회원ID', '작성일시', '리뷰내용', '감정키워드', '평점']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for review in all_data:
                row = {
                    '리뷰번호': review.get('revwNum', ''),
                    '회원ID': review.get('mmbrId', ''),
                    '작성일시': review.get('cretDttm', ''),
                    '리뷰내용': review.get('revwCntt', ''),
                    '감정키워드': review.get('revwEmtnKywrName', ''),
                    '평점': review.get('revwRvgr', '')
                }
                writer.writerow(row)
        
        return f"총 {len(all_data)}개의 리뷰가 '{filepath}' 파일에 저장되었습니다."
    else:
        return "수집된 리뷰가 없습니다."

def save_reviews(reviews, book_code):
    """리뷰 데이터를 CSV 파일로 저장"""
    if not reviews:
        print("저장할 리뷰가 없습니다.")
        return
    
    # data 디렉토리 생성
    os.makedirs('data', exist_ok=True)
    
    # 파일명 생성
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/교보_{book_code}_리뷰_{timestamp}.csv"
    
    # DataFrame 생성 및 저장
    df = pd.DataFrame(reviews)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"\n총 {len(reviews)}개의 리뷰가 '{filename}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    # 사용 예시
    # 인문 카테고리(118) 도서 목록 스크랩
    # print(scrap_category_book_list("118"))
    
    # 특정 도서의 리뷰 스크랩 (예: S000061818273)
    # print(scrap_review("S000061818273"))
    
    # 명령줄에서 실행 시
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "book":
            if len(sys.argv) > 2:
                result = scrap_category_book_list(sys.argv[2])
                print(result)
            else:
                print("카테고리 코드를 입력하세요. 예: python script.py book 118")
        elif sys.argv[1] == "review":
            if len(sys.argv) > 2:
                result = scrap_review(sys.argv[2])
                print(result)
            else:
                print("도서 코드를 입력하세요. 예: python script.py review S000061818273")
        else:
            print("사용법: python script.py [book|review] [코드]")
    else:
        print("사용법: python script.py [book|review] [코드]")