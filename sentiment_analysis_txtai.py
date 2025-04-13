# pip install pandas matplotlib wordcloud txtai

import os
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime
from txtai.embeddings import Embeddings
import numpy as np
import argparse

def parse_arguments():
    """명령행 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='도서 리뷰 감성 분석 및 리포트 생성',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '-t', '--title',
        required=True,
        help='도서 제목 (예: "세이노의 가르침")'
    )
    
    parser.add_argument(
        '-f', '--file',
        required=True,
        help='리뷰 데이터 CSV 파일 경로\n' + 
             '(예: data/reviews.csv)\n' +
             '필수 컬럼: 리뷰번호,회원ID,작성일시,리뷰내용,감정키워드,평점'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='결과물 저장 경로 (예: output/book_report.html)\n' +
             '지정하지 않으면 output/도서제목_report.html로 저장'
    )
    
    return parser.parse_args()

# 📁 경로 설정
def setup_paths(args):
    """경로 설정"""
    # 도서 제목에서 파일명으로 사용할 수 없는 문자 제거
    safe_title = args.title.replace('"', '').replace(' ', '_')
    
    # 출력 디렉토리와 파일명 설정
    if args.output:
        OUTPUT_DIR = os.path.dirname(args.output)
        report_filename = os.path.basename(args.output)
    else:
        OUTPUT_DIR = 'output'
        report_filename = f"{safe_title}_report.html"
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    return {
        'input_csv': args.file,
        'output_dir': OUTPUT_DIR,
        'wordcloud_path': os.path.join(OUTPUT_DIR, f"{safe_title}_wordcloud.png"),
        'report_html_path': os.path.join(OUTPUT_DIR, report_filename),
        'font_path': "data/NanumGothic.ttf"
    }

# 🧠 txtai 인덱스 생성
def build_txtai_index():
    """
    txtai 임베딩 인덱스를 생성하고 감정 기준 샘플 문장을 인덱싱함
    """
    index = Embeddings({"path": "sentence-transformers/all-MiniLM-L6-v2"})

    samples = [
        ("positive", "이 책은 정말 유익하고 감동적이었어요."),
        ("positive", "내용이 흥미롭고 유용했어요."),
        ("positive", "재미있고 다시 읽고 싶어요."),
        ("negative", "별로 도움이 안 됐어요."),
        ("negative", "실망스럽고 지루했어요."),
        ("negative", "읽기 힘들고 후회돼요.")
    ]

    documents = [(i, text, {"label": label}) for i, (label, text) in enumerate(samples)]
    index.index(documents)
    return index

# 🧠 리뷰 텍스트에 대한 감성 예측
def predict_sentiment(txtai_index, text):
    """
    txtai 임베딩 인덱스를 이용해 텍스트의 감정 레이블을 추론
    """
    results = txtai_index.search(text, 1)
    if results:
        docid = results[0][0]
        # docid를 기반으로 감정 레이블을 추정
        # 예: 0~2는 긍정, 3~5는 부정
        if int(docid) <= 2:
            return "positive"
        else:
            return "negative"
    return "neutral"
    

# 🧠 감정 레이블을 감성 점수(0~1)로 변환
def label_to_score(label):
    """
    감정 레이블을 점수로 변환 (긍정=1.0, 부정=0.0)
    """
    return {"positive": 1.0, "negative": 0.0}.get(label, 0.5)

# 🧠 시계열용 감성 데이터 생성
def analyze_sentiments(df, txtai_index):
    """
    리뷰내용에 대한 감정 분석을 수행하고 감성 점수를 추가
    """
    df["예측감정"] = df["리뷰내용"].apply(lambda x: predict_sentiment(txtai_index, x))
    df["감성점수"] = df["예측감정"].apply(label_to_score)
    df["작성일시"] = pd.to_datetime(df["작성일시"])
    return df.sort_values("작성일시")

# 📊 감정키워드 분포 계산
def extract_emotion_keywords(df):
    """
    감정키워드 문자열을 분해하여 분포 집계
    """
    all_keywords = []
    for entry in df["감정키워드"].dropna():
        all_keywords.extend([kw.strip() for kw in entry.split(",")])
    return dict(Counter(all_keywords))

# 🌥 워드클라우드 이미지 생성
def generate_wordcloud(texts, font_path, output_path):
    """
    리뷰 내용을 기반으로 컬러풀한 사각형 워드클라우드 생성 및 저장
    """
    text = " ".join(texts.dropna())
    
    wc = WordCloud(
        font_path=font_path,
        width=800,
        height=800,  # 가로 세로 동일한 크기로 변경
        background_color="white",
        colormap='viridis',
        prefer_horizontal=0.7,
        min_font_size=10,
        max_font_size=100,
        relative_scaling=0.5,
        random_state=42,  # 일관된 색상을 위한 시드 설정
        collocations=True,
        regexp=r"\w[\w']+",
    )
    
    try:
        wc.generate(text)
        plt.figure(figsize=(10, 10))  # 정사각형 크기로 설정
        plt.imshow(wc, interpolation='bilinear')
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.savefig(output_path, dpi=400, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"워드클라우드 생성 중 오류 발생: {e}")

# 📄 HTML 보고서 생성
def generate_html_report(keyword_dist, df_sorted, wordcloud_path, output_path, book_title):
    """
    Tailwind CSS를 적용한 모던한 HTML 보고서 생성
    """
    keyword_labels = list(keyword_dist.keys())
    keyword_counts = list(keyword_dist.values())

    # 월별 평점 데이터 집계
    df_sorted['월'] = df_sorted['작성일시'].dt.strftime('%Y-%m')
    monthly_ratings = df_sorted.groupby('월')['평점'].agg(['mean', 'count']).round(2)
    monthly_ratings = monthly_ratings[monthly_ratings['count'] >= 1]  # 최소 1개 이상의 데이터가 있는 월만 선택
    
    date_labels = monthly_ratings.index.tolist()
    rating_series = monthly_ratings['mean'].tolist()
    review_counts = monthly_ratings['count'].tolist()

    avg_rating = df_sorted['평점'].mean()
    summary = "전반적으로 높은 평점입니다." if avg_rating > 4.0 else "개선이 필요한 부분이 있습니다."

    insights = [
        "긍정적 리뷰가 많이 포함되어 있습니다.",
        f"전체 평균 평점은 {avg_rating:.1f}점 입니다.",
        "주요 감정키워드는 추천해요, 최고예요, 쉬웠어요 등이 포함됩니다.",
        "부정 리뷰는 대체로 평점 3점 이하와 연관되어 있습니다.",
        "감성 키워드는 마케팅 인사이트로 활용 가능합니다."
    ]

    # 상위 5개 감정 키워드 추출
    top_keywords = sorted(keyword_dist.items(), key=lambda x: x[1], reverse=True)[:5]
    top_keyword_text = ", ".join([f"{kw}({count}회)" for kw, count in top_keywords])

    # 평점 통계
    rating_stats = df_sorted['평점'].agg(['mean', 'min', 'max', 'count']).round(2)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{book_title} - 도서 리뷰 분석 리포트</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-white text-gray-800 min-h-screen p-8">
    <div class="max-w-6xl mx-auto">
        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h1 class="text-4xl font-bold text-center mb-2">📚 도서 리뷰 분석 리포트</h1>
            <h2 class="text-2xl text-gray-600 text-center mb-6">"{book_title}"</h2>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-semibold mb-4">1. 감정 키워드 분포</h2>
                <canvas id="keywordChart"></canvas>
            </div>
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-2xl font-semibold mb-4">2. 리뷰 워드클라우드</h2>
                <img src="{os.path.basename(wordcloud_path)}" class="w-full">
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-semibold mb-4">3. 월별 평점 및 리뷰 수 추이</h2>
            <canvas id="ratingChart"></canvas>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6 mb-8">
            <h2 class="text-2xl font-semibold mb-4">4. 종합 분석</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-2">📊 평점 분석</h3>
                    <ul class="space-y-1">
                        <li>평균 평점: {rating_stats['mean']:.1f}점</li>
                        <li>최저 평점: {rating_stats['min']:.1f}점</li>
                        <li>최고 평점: {rating_stats['max']:.1f}점</li>
                        <li>전체 리뷰 수: {rating_stats['count']:,}개</li>
                    </ul>
                </div>
                <div class="bg-gray-50 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold mb-2">🔑 주요 감정 키워드</h3>
                    <p class="leading-relaxed">{top_keyword_text}</p>
                </div>
            </div>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6">
            <h2 class="text-2xl font-semibold mb-4">5. 비즈니스 인사이트</h2>
            <ul class="list-disc pl-6 space-y-2">
                {''.join(f"<li class='text-lg'>{insight}</li>" for insight in insights)}
            </ul>
        </div>
    </div>

<script>
const ctx1 = document.getElementById('keywordChart');
new Chart(ctx1, {{
    type: 'bar',
    data: {{
        labels: {keyword_labels},
        datasets: [{{
            label: '감정 키워드 빈도수',
            data: {keyword_counts},
            backgroundColor: 'rgba(0, 0, 0, 0.8)'
        }}]
    }},
    options: {{
        plugins: {{
            legend: {{
                display: false
            }}
        }},
        scales: {{
            y: {{
                beginAtZero: true,
                grid: {{
                    color: 'rgba(0, 0, 0, 0.1)'
                }}
            }},
            x: {{
                grid: {{
                    display: false
                }}
            }}
        }}
    }}
}});

const ctx2 = document.getElementById('ratingChart');
new Chart(ctx2, {{
    type: 'line',
    data: {{
        labels: {date_labels},
        datasets: [
            {{
                label: '평균 평점',
                data: {rating_series},
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                fill: true,
                tension: 0.3,
                yAxisID: 'y',
                borderWidth: 2
            }},
            {{
                label: '리뷰 수',
                data: {review_counts},
                borderColor: 'rgb(255, 99, 132)',
                backgroundColor: 'rgba(255, 99, 132, 0.1)',
                fill: true,
                tension: 0.3,
                yAxisID: 'y1',
                borderWidth: 2
            }}
        ]
    }},
    options: {{
        interaction: {{
            mode: 'index',
            intersect: false,
        }},
        plugins: {{
            title: {{
                display: true,
                text: ['월별 평균 평점 및 리뷰 수 변화 추이', '(평점: 좌측 축, 리뷰 수: 우측 축)'],
                font: {{
                    size: 16,
                    weight: 'bold'
                }},
                padding: 20
            }},
            legend: {{
                position: 'top',
                labels: {{
                    usePointStyle: true,
                    padding: 15
                }}
            }}
        }},
        scales: {{
            y: {{
                type: 'linear',
                position: 'left',
                min: 0,
                max: 5,
                title: {{
                    display: true,
                    text: '평균 평점 (0-5)'
                }},
                grid: {{
                    color: 'rgba(75, 192, 192, 0.1)'
                }},
                ticks: {{
                    color: 'rgb(75, 192, 192)'
                }}
            }},
            y1: {{
                type: 'linear',
                position: 'right',
                min: 0,
                title: {{
                    display: true,
                    text: '리뷰 수'
                }},
                grid: {{
                    display: false
                }},
                ticks: {{
                    color: 'rgb(255, 99, 132)'
                }}
            }},
            x: {{
                title: {{
                    display: true,
                    text: '월별'
                }},
                grid: {{
                    display: false
                }}
            }}
        }}
    }}
}});
</script>
</body>
</html>
""")

# ✅ 메인 실행 함수
def main():
    """메인 함수"""
    # 명령행 인자 파싱
    args = parse_arguments()
    
    # 경로 설정
    paths = setup_paths(args)
    
    # CSV 파일 읽기
    try:
        df = pd.read_csv(paths['input_csv'])
        required_columns = ['리뷰번호', '회원ID', '작성일시', '리뷰내용', '감정키워드', '평점']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"CSV 파일에 필수 컬럼이 없습니다: {', '.join(missing_columns)}")
    except Exception as e:
        print(f"CSV 파일 읽기 오류: {str(e)}")
        return
    
    # 데이터 전처리
    df_sorted = analyze_sentiments(df, build_txtai_index())
    
    # 감정 키워드 분포 계산
    keyword_dist = extract_emotion_keywords(df_sorted)
    
    # 워드클라우드 생성
    try:
        generate_wordcloud(df_sorted["리뷰내용"], paths['font_path'], paths['wordcloud_path'])
    except Exception as e:
        print(f"워드클라우드 생성 오류: {str(e)}")
        return
    
    # HTML 리포트 생성
    try:
        generate_html_report(keyword_dist, df_sorted, paths['wordcloud_path'], paths['report_html_path'], args.title)
        print(f"\n✨ 분석 완료! 결과물 위치:")
        print(f"- 워드클라우드: {paths['wordcloud_path']}")
        print(f"- HTML 리포트: {paths['report_html_path']}")
    except Exception as e:
        print(f"리포트 생성 오류: {str(e)}")
        return

if __name__ == "__main__":
    main()