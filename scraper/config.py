import os

# 실행 순서 (30분 단위 로테이션)
CATEGORY_ORDER = ["K-Pop", "K-Drama", "K-Movie", "K-Entertain", "K-Culture"]

# 1차 광범위 검색 키워드 (API용)
SEARCH_KEYWORDS = {
    "K-Pop": "아이돌 컴백 1위 빌보드",
    "K-Drama": "드라마 시청률 화제성",
    "K-Movie": "한국 영화 박스오피스 개봉작",
    "K-Entertain": "예능 시청률 레전드",
    "K-Culture": "서울 핫플레이스 팝업스토어 여행"
}

# DB 보관 최대 개수
MAX_ITEMS_PER_CATEGORY = 30
