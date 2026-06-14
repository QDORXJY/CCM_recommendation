import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="CCM Search", layout="wide")
st.title("CCM 찬양 검색 대시보드")

# 2. 데이터 로드 (캐싱을 통해 속도 향상)
@st.cache_data
def load_data():
    return pd.read_csv("ccm_database_keywords_ranked_final.csv")

df = load_data()

# 3. 데이터 전처리 및 전체 키워드 목록 추출
# 결측치 방지 및 고유 키워드 추출
all_keywords = set()
for keywords in df['keyword'].dropna():
    for k in keywords.split(','):
        all_keywords.add(k.strip())
keyword_list = sorted(list(all_keywords))

# 4. 사이드바(Sidebar) UI 설정
st.sidebar.header("검색 필터")
search_text = st.sidebar.text_input("제목 또는 아티스트 검색")
selected_keywords = st.sidebar.multiselect("주제 키워드 선택", keyword_list)

# 5. 검색 및 필터링 로직
filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_text, case=False, na=False) |
        filtered_df['artist'].str.contains(search_text, case=False, na=False)
    ]

if selected_keywords:
    for kw in selected_keywords:
        filtered_df = filtered_df[filtered_df['keyword'].str.contains(kw, case=False, na=False)]

# 6. 결과 출력
st.write(f"### 검색 결과: 총 {len(filtered_df)}곡")
st.dataframe(
    filtered_df[['artist', 'title', 'keyword', 'lyrics']],
    use_container_width=True,
    hide_index=True
)