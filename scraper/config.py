# scraper/config.py

# 실행 순서 (30분마다 하나씩 순환)
CATEGORY_ORDER = ["K-Pop", "K-Drama", "K-Movie", "K-Entertain", "K-Culture"]

# 카테고리별 1차 광범위 검색 키워드 (트렌드 파악용)
SEARCH_KEYWORDS = {
    "K-Pop": "아이돌 컴백 1위 빌보드 음원",
    "K-Drama": "드라마 시청률 화제성",
    "K-Movie": "한국 영화 박스오피스 개봉작 반응",
    "K-Entertain": "예능 시청률 레전드 출연",
    "K-Culture": "서울 핫플레이스 팝업스토어 여행 맛집"
}

# DB에 유지할 카테고리별 최대 기사 수
MAX_ITEMS_PER_CATEGORY = 30
