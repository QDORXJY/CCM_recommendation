import streamlit as st
import pandas as pd
import urllib.parse

# 1. 페이지 기본 설정
st.set_page_config(page_title="CCM Search Pro", layout="wide")

# 2. 레이아웃 최적화 CSS
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        font-size: 1.4rem !important;
    }
    [data-testid="stSidebar"] {
        font-size: 1.2rem !important;
    }
    h1 {
        font-size: 2.8rem !important;
        padding-bottom: 2rem;
    }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("CCM 찬양 검색 대시보드")

# 3. 데이터 로드 및 전처리
@st.cache_data
def load_data():
    df = pd.read_csv("ccm_database_keywords_popularity_labeled.csv")
    
    # 결측치 방지
    df['keyword_1'] = df['keyword_1'].fillna('-')
    df['keyword_2'] = df['keyword_2'].fillna('-')
    df['keyword_3'] = df['keyword_3'].fillna('-')
    df['popularity_score'] = df['popularity_score'].fillna(0).astype(int)
    df['popularity_label'] = df['popularity_label'].fillna('unknown')
    
    # 인지도 등급(및 점수) 통합 컬럼 생성
    df['인지도 등급(점수)'] = df.apply(
        lambda row: f"{row['popularity_label'].upper()} ({row['popularity_score']}점)", axis=1
    )
    
    # 유튜브 검색 URL 동적 생성
    df['youtube_url'] = df.apply(
        lambda row: "https://www.youtube.com/results?search_query=" + 
                    urllib.parse.quote(f"{row['artist']} {row['title']} official"), axis=1
    )
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("ccm_database_keywords_popularity_labeled.csv 파일을 찾을 수 없습니다.")
    st.stop()

# 4. 사이드바 검색 및 필터 구조
st.sidebar.header("검색 필터")
search_text = st.sidebar.text_input("제목 또는 아티스트 검색")

# 검색을 위한 고유 키워드 풀 추출
all_keywords = set()
for col in ['keyword_1', 'keyword_2', 'keyword_3']:
    for k in df[col].dropna().unique():
        if k != '-':
            all_keywords.add(k.strip())
keyword_list = sorted(list(all_keywords))

# 다중 선택 (사용자가 선택한 순서가 리스트의 인덱스로 유지됨)
selected_keywords = st.sidebar.multiselect("핵심 키워드 선택 (선택한 순서대로 정렬 우선순위 부여)", keyword_list)

# 5. 데이터 필터링 및 서순 기반 가중치 정렬 로직
filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_text, case=False, na=False) |
        filtered_df['artist'].str.contains(search_text, case=False, na=False)
    ]

# 매칭 점수 산출 함수 (핵심 로직)
def calculate_match_score(row, selected_kws):
    if not selected_kws:
        return 0
    
    total_score = 0
    # 선택한 키워드 개수를 기반으로 최고 가중치 설정
    max_order_weight = len(selected_kws)
    
    for index, kw in enumerate(selected_kws):
        # 먼저 선택할수록 높은 가중치 부여 (예: 3개 선택 시 첫 번째 키워드는 3점, 두 번째는 2점, 세 번째는 1점)
        order_weight = max_order_weight - index
        
        # 곡 내부의 키워드 순위별 가중치 (1순위=10점, 2순위=5점, 3순위=2점)
        if row['keyword_1'] == kw:
            total_score += (order_weight * 10)
        elif row['keyword_2'] == kw:
            total_score += (order_weight * 5)
        elif row['keyword_3'] == kw:
            total_score += (order_weight * 2)
            
    return total_score

if selected_keywords:
    # 1단계: 선택된 키워드 중 최소 하나라도 포함된 곡들만 필터링 (OR 조건으로 확장하여 서순 매칭 유도)
    filtered_df = filtered_df[
        filtered_df['keyword_1'].isin(selected_keywords) |
        filtered_df['keyword_2'].isin(selected_keywords) |
        filtered_df['keyword_3'].isin(selected_keywords)
    ]
    
    # 2단계: 각 행별 매칭 점수 계산 계산
    filtered_df['match_score'] = filtered_df.apply(lambda r: calculate_match_score(r, selected_keywords), axis=1)
    
    # 3단계: 매칭 점수 높은 순(서순 일치) -> 동점일 경우 인지도 점수 높은 순으로 최종 정렬
    filtered_df = filtered_df.sort_values(by=["match_score", "popularity_score"], ascending=[False, False])
else:
    # 키워드를 선택하지 않았을 때는 기본 인지도순 정렬
    filtered_df = filtered_df.sort_values(by="popularity_score", ascending=False)

# 6. 요구사항에 맞춘 컬럼 매핑
display_cols = {
    'artist': '아티스트',
    'title': '곡 제목',
    'keyword_1': '핵심 키워드 (1순위)',
    'keyword_2': '핵심 키워드 (2순위)',
    'keyword_3': '핵심 키워드 (3순위)',
    'youtube_url': '유튜브 링크',
    'lyrics': '가사',
    '인지도 등급(점수)': '인지도 등급(점수)'
}

render_df = filtered_df[list(display_cols.keys())].rename(columns=display_cols)

st.write(f"#### 🔍 검색 결과: 총 {len(render_df)}곡")

# 7. 화면 배치 및 렌더링
st.dataframe(
    render_df,
    column_config={
        "유튜브 링크": st.column_config.LinkColumn("유튜브 링크", display_text="🎵 유튜브 검색"),
        "가사": st.column_config.TextColumn("가사", width="large")
    },
    use_container_width=True,
    hide_index=True,
    height=800
)
