import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="CCM Search Pro", layout="wide")

# [수정됨] 표(Dataframe) 렌더링을 망가뜨리던 전체 폰트 확대 코드를 제거하고, 
# 사이드바와 제목 등 안전한 곳에만 크기 확장을 적용합니다.
st.markdown("""
    <style>
    /* 사이드바 글씨 크기 약간 확대 */
    [data-testid="stSidebar"] * {
        font-size: 1.1rem !important;
    }
    /* 제목 크기 및 여백 최적화 */
    h1 {
        font-size: 2.5rem !important;
        padding-bottom: 1rem;
    }
    /* 하단 찌부 방지 (전체 너비 사용) */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("CCM 찬양 검색 대시보드")

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

st.sidebar.header("검색 필터")
search_text = st.sidebar.text_input("제목 또는 아티스트 검색")

all_keywords = set()
for col in ['keyword_1', 'keyword_2', 'keyword_3']:
    for k in df[col].dropna().unique():
        if k != '-':
            all_keywords.add(k.strip())
keyword_list = sorted(list(all_keywords))

selected_keywords = st.sidebar.multiselect("핵심 키워드 선택 (다중 선택 가능)", keyword_list)

filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_text, case=False, na=False) |
        filtered_df['artist'].str.contains(search_text, case=False, na=False)
    ]

if selected_keywords:
    for kw in selected_keywords:
        filtered_df = filtered_df[
            (filtered_df['keyword_1'] == kw) |
            (filtered_df['keyword_2'] == kw) |
            (filtered_df['keyword_3'] == kw)
        ]

filtered_df = filtered_df.sort_values(by="popularity_score", ascending=False)

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