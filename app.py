import streamlit as st
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="CCM Search Pro", layout="wide")
st.title("CCM 찬양 검색 대시보드 (인지도 및 키워드 기반)")

# 2. 데이터 로드 (캐싱)
@st.cache_data
def load_data():
    df = pd.read_csv("ccm_database_keywords_popularity_labeled.csv")
    # 결측치 처리 방어 로직
    df['popularity_score'] = df['popularity_score'].fillna(0)
    df['popularity_label'] = df['popularity_label'].fillna('unknown')
    return df

df = load_data()

# 3. 데이터 전처리 및 키워드 목록 추출
all_keywords = set()
for keywords in df['keyword'].dropna():
    for k in str(keywords).split(','):
        all_keywords.add(k.strip())
keyword_list = sorted(list(all_keywords))

# 4. 사이드바(Sidebar) UI 설정 - 필터 및 정렬
st.sidebar.header("검색 및 필터")
search_text = st.sidebar.text_input("제목 또는 아티스트 검색")

selected_keywords = st.sidebar.multiselect("주제 키워드 선택", keyword_list)

# 인지도 필터 추가
popularity_options = ["전체 보기"] + list(df['popularity_label'].dropna().unique())
selected_popularity = st.sidebar.selectbox("인지도 등급 필터", popularity_options)

st.sidebar.markdown("---")

# 인지도 점수 정렬 옵션 추가
sort_by = st.sidebar.radio("결과 정렬 기준", [
    "인지도 (높은순)", 
    "인지도 (낮은순)", 
    "제목 (가나다순)", 
    "아티스트 (가나다순)"
])

# 5. 검색 및 필터링 적용 로직
filtered_df = df.copy()

if search_text:
    filtered_df = filtered_df[
        filtered_df['title'].str.contains(search_text, case=False, na=False) |
        filtered_df['artist'].str.contains(search_text, case=False, na=False)
    ]

if selected_keywords:
    for kw in selected_keywords:
        filtered_df = filtered_df[filtered_df['keyword'].str.contains(kw, case=False, na=False)]

if selected_popularity != "전체 보기":
    filtered_df = filtered_df[filtered_df['popularity_label'] == selected_popularity]

# 6. 정렬 적용 로직
if sort_by == "인지도 (높은순)":
    filtered_df = filtered_df.sort_values(by="popularity_score", ascending=False)
elif sort_by == "인지도 (낮은순)":
    filtered_df = filtered_df.sort_values(by="popularity_score", ascending=True)
elif sort_by == "제목 (가나다순)":
    filtered_df = filtered_df.sort_values(by="clean_title", ascending=True)
elif sort_by == "아티스트 (가나다순)":
    filtered_df = filtered_df.sort_values(by="artist", ascending=True)

# 7. 화면 출력
st.write(f"### 🔍 검색 결과: 총 {len(filtered_df)}곡")

# 사용자에게 깔끔하게 보여주기 위한 컬럼 한글화 및 선택
display_cols = ['artist', 'title', 'keyword', 'popularity_score', 'popularity_label', 'lyrics']
display_df = filtered_df[display_cols].rename(columns={
    'artist': '아티스트',
    'title': '곡 제목',
    'keyword': '핵심 키워드',
    'popularity_score': '인지도 점수 (100점 만점)',
    'popularity_label': '인지도 등급',
    'lyrics': '가사 일부'
})

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)