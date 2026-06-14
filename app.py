import streamlit as st
import pandas as pd
import urllib.parse

# 1. 페이지 기본 설정
st.set_page_config(page_title="CCM Search Pro", layout="wide")

# 2. 글씨 크기 1.5배 증폭 및 레이아웃 최적화 CSS
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
    # 업로드된 파일명으로 매핑
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
    
    # API 불필요, 봇 차단 우회용 유튜브 검색 URL 동적 생성
    df['youtube_url'] = df.apply(
        lambda row: "https://www.youtube.com/results?search_query=" + 
                    urllib.parse.quote(f"{row['artist']} {row['title']} official"), axis=1
    )
    
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("ccm_database_keywords_popularity_labeled.csv 파일을 찾을 수 없습니다. 파일명을 확인하십시오.")
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

selected_keyword = st.sidebar.selectbox("핵심 키워드 필터 (전체 검색)", ["전체"] + keyword_list)

# 5. 데이터 필터링 로직
filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_text, case=False, na=False) |
        filtered_df['artist'].str.contains(search_text, case=False, na=False)
    ]

if selected_keyword != "전체":
    filtered_df = filtered_df[
        (filtered_df['keyword_1'] == selected_keyword) |
        (filtered_df['keyword_2'] == selected_keyword) |
        (filtered_df['keyword_3'] == selected_keyword)
    ]

# 인지도 높은 순 기본 정렬
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

# 7. 화면 배치 고도화 (찌부 현상 방지 및 링크 컬럼 설정)
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