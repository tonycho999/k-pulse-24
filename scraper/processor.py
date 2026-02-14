# scraper/processor.py
import time
from datetime import datetime
import config
import naver_api
import gemini_api
import database

def run_category_process(category):
    print(f"\n🚀 [Processing] Category: {category}")

    # 1. 초기 뉴스 수집
    keyword = config.SEARCH_KEYWORDS.get(category)
    print(f"   1️⃣ Fetching base news for '{keyword[:10]}...'")
    raw_items = naver_api.search_news_api(keyword, display=100)
    
    if not raw_items:
        print("   ❌ [Stop] No items found.")
        return

    titles = "\n".join([f"- {item['title']}" for item in raw_items])

    # 2. 랭킹 & 검색 키워드 추출 (여기가 핵심)
    print("   2️⃣ Extracting Keywords (Subject vs Person)...")

    # 카테고리별 맞춤형 지시사항 (User Rule 적용)
    if category == "K-Pop":
        rule = """
        - Target(DB): Must be the **SONG TITLE** (e.g., 'Super Shy', 'Dynamite').
        - Search: Must be the **ARTIST/GROUP NAME** (e.g., 'NewJeans', 'BTS').
        """
    elif category == "K-Drama":
        rule = """
        - Target(DB): Must be the **DRAMA TITLE** (e.g., 'Squid Game').
        - Search: Must be the **MAIN ACTOR/ACTRESS Name** (e.g., 'Lee Jung-jae').
        """
    elif category == "K-Movie":
        rule = """
        - Target(DB): Must be the **MOVIE TITLE** (e.g., 'Exhuma').
        - Search: Must be the **MAIN ACTOR/ACTRESS Name** (e.g., 'Choi Min-sik').
        """
    elif category == "K-Entertain":
        rule = """
        - Target(DB): Must be the **SHOW TITLE** (e.g., 'Running Man').
        - Search: Must be the **CAST MEMBER Name** (e.g., 'Yoo Jae-suk').
        """
    else: # K-Culture
        rule = """
        - Target(DB): Must be the Place, Food, or Tradition Name (English).
        - Search: Korean Name of the Place/Food.
        - **CRITICAL**: EXCLUDE ANY IDOLS, SINGERS, ACTORS, or K-POP GROUPS.
        - If the news is about an idol visiting a place, IGNORE IT.
        """

    rank_prompt = f"""
    [Task]
    Analyze these news titles about {category}.
    Extract Top 10 trends following these STRICT rules:
    {rule}

    [Output JSON]
    {{ 
      "rankings": [ 
        {{ 
          "rank": 1, 
          "display_title_en": "English Title for DB", 
          "search_keyword_kr": "Korean Name for Searching", 
          "meta": "Short Info", 
          "score": 95 
        }} 
      ] 
    }}
    """
    
    rank_res = gemini_api.ask_gemini(rank_prompt)
    if not rank_res: return

    rankings = rank_res.get("rankings", [])[:10]
    
    # 랭킹 저장 (DB에는 제목/노래제목이 들어감)
    db_rankings = []
    for item in rankings:
        db_rankings.append({
            "category": category,
            "rank": item.get("rank"),
            "title": item.get("display_title_en"), # 제목 (영어)
            "meta_info": item.get("meta", ""),
            "score": item.get("score", 0),
            "updated_at": datetime.now().isoformat()
        })
    database.save_rankings_to_db(db_rankings)

    # 3. 타겟 선정 (도배 방지)
    print("   3️⃣ Selecting Target...")
    target_display = ""  # DB 저장용 (제목)
    target_search = ""   # 네이버 검색용 (사람)
    
    for item in rankings:
        d_title = item.get("display_title_en")
        s_word = item.get("search_keyword_kr")
        
        # 쿨타임 체크는 '제목(DB키)' 기준으로 함
        if database.is_keyword_used_recently(category, d_title, hours=4):
            print(f"      - Skip '{d_title}' (Cooldown)")
        else:
            print(f"      - Selected: '{d_title}' (Search: {s_word})")
            target_display = d_title
            target_search = s_word
            break
    
    if not target_display and rankings:
        target_display = rankings[0].get("display_title_en")
        target_search = rankings[0].get("search_keyword_kr")

    if not target_display: return

    # 4. 정밀 검색 (지시하신 대로 '사람 이름'으로 검색)
    print(f"   4️⃣ Searching Naver for '{target_search}'...")
    target_items = naver_api.search_news_api(target_search, display=5)
    
    full_texts = []
    target_link = ""
    target_image = ""

    for item in target_items:
        link = item['link']
        crawled = naver_api.crawl_article(link)
        if crawled['text']:
            full_texts.append(crawled['text'])
            if not target_image: target_image = crawled['image']
            if not target_link: target_link = link
        else:
            full_texts.append(item['description'])
            if not target_link: target_link = link

    if not full_texts: return

    # 5. 요약 작성 (영어)
    print(f"   5️⃣ Summarizing '{target_display}'...")
    summary_prompt = f"""
    [Context]
    Category: {category}
    Main Subject: {target_display}
    Person involved: {target_search}
    
    [Source Articles (Korean)]
    {str(full_texts)[:6000]}

    [Task]
    Write a news summary in **ENGLISH**.
    - Title: Must be about '{target_display}' (The Song/Drama/Movie).
    - Content: Summarize the news, focusing on why '{target_search}' (The Person) is in the news regarding '{target_display}'.

    [Output JSON]
    {{ "title": "English Title", "summary": "English Summary..." }}
    """
    
    sum_res = gemini_api.ask_gemini(summary_prompt)
    
    if sum_res:
        news_item = {
            "category": category,
            "keyword": target_display, # DB에는 노래/드라마 제목 저장
            "title": sum_res.get("title", f"News about {target_display}"),
            "summary": sum_res.get("summary", ""),
            "link": target_link,
            "image_url": target_image,
            "score": 100,
            "created_at": datetime.now().isoformat(),
            "likes": 0
        }
        
        # 6. 저장
        database.save_news_to_live([news_item])
        database.save_news_to_archive([news_item])
        database.cleanup_old_data(category, config.MAX_ITEMS_PER_CATEGORY)
        print("   🎉 SUCCESS!")
