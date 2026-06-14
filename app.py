import streamlit as st
import pandas as pd
import urllib.parse
import re

# 1. 페이지 기본 설정
st.set_page_config(page_title="CCM Search Pro", layout="wide")

# 2. 레이아웃 CSS
st.markdown("""
    <style>
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
    
    df['keyword_1'] = df['keyword_1'].fillna('-')
    df['keyword_2'] = df['keyword_2'].fillna('-')
    df['keyword_3'] = df['keyword_3'].fillna('-')
    df['popularity_score'] = df['popularity_score'].fillna(0).astype(int)
    df['popularity_label'] = df['popularity_label'].fillna('unknown')
    
    df['인지도 등급(점수)'] = df.apply(
        lambda row: f"{row['popularity_label'].upper()} ({row['popularity_score']}점)", axis=1
    )
    
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

# 4. 사이드바 UI
st.sidebar.header("검색 필터")
# 검색 범위를 가사까지 확장했음을 명시
search_text = st.sidebar.text_input("제목, 아티스트 또는 가사 검색")

all_keywords = set()
for col in ['keyword_1', 'keyword_2', 'keyword_3']:
    for k in df[col].dropna().unique():
        if k != '-':
            all_keywords.add(k.strip())
keyword_list = sorted(list(all_keywords))

selected_keywords = st.sidebar.multiselect("핵심 키워드 선택 (선택한 순서대로 정렬 가중치 부여)", keyword_list)

filtered_df = df.copy()

# 5. 데이터 필터링 및 정렬

# [수정됨] 단어(Token) 단위 분할 및 가사 포함 검색 로직
if search_text:
    search_tokens = search_text.split() # 띄어쓰기 기준으로 단어 분리
    
    for token in search_tokens:
        filtered_df = filtered_df[
            filtered_df['title'].astype(str).str.contains(token, case=False, na=False) |
            filtered_df['artist'].astype(str).str.contains(token, case=False, na=False) |
            filtered_df['lyrics'].astype(str).str.contains(token, case=False, na=False)
        ]

# 가중치 산출 함수
def calculate_match_score(row, selected_kws):
    if not selected_kws:
        return 0
    total_score = 0
    max_order_weight = len(selected_kws)
    
    for index, kw in enumerate(selected_kws):
        order_weight = max_order_weight - index
        if row['keyword_1'] == kw:
            total_score += (order_weight * 10)
        elif row['keyword_2'] == kw:
            total_score += (order_weight * 5)
        elif row['keyword_3'] == kw:
            total_score += (order_weight * 2)
    return total_score

# 다중 키워드 AND 조건 적용
if selected_keywords:
    for kw in selected_keywords:
        filtered_df = filtered_df[
            (filtered_df['keyword_1'] == kw) |
            (filtered_df['keyword_2'] == kw) |
            (filtered_df['keyword_3'] == kw)
        ]
    
    filtered_df['match_score'] = filtered_df.apply(lambda r: calculate_match_score(r, selected_keywords), axis=1)
    filtered_df = filtered_df.sort_values(by=["match_score", "popularity_score"], ascending=[False, False])
else:
    filtered_df = filtered_df.sort_values(by="popularity_score", ascending=False)

# 6. 화면 출력
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
