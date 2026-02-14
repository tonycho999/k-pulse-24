# scraper/processor.py
import time
from datetime import datetime
import config
import naver_api
import gemini_api
import database

def run_category_process(category):
    print(f"\n🚀 [Processing] Category: {category}")

    # 1. [수정됨] 3개의 키워드로 각각 검색 후 결과 합치기
    queries = config.SEARCH_QUERIES.get(category, [])
    all_raw_items = []
    seen_links = set() # 중복 기사 제거용

    print(f"   1️⃣ Fetching news with 3 queries...")
    
    for q in queries:
        print(f"      - Query: '{q}'")
        # 각 쿼리당 20개씩 수집 (총 60개 확보)
        items = naver_api.search_news_api(q, display=20)
        
        for item in items:
            # 중복 제거 (링크 기준)
            if item['link'] not in seen_links:
                seen_links.add(item['link'])
                all_raw_items.append(item)
        
        time.sleep(0.5) # API 매너 호출

    if not all_raw_items:
        print("   ❌ [Stop] No items found from all queries.")
        return

    print(f"      ✅ Total collected articles: {len(all_raw_items)}")
    
    # AI에게 보낼 기사 제목 리스트 생성
    titles = "\n".join([f"- {item['title']}" for item in all_raw_items])

    # 2. 랭킹 & 검색 키워드 추출
    print("   2️⃣ Extracting Keywords (Subject vs Person)...")

    # 카테고리별 규칙 (지난번과 동일)
    if category == "K-Pop":
        rule = """
        - Target(DB): **SONG TITLE** (e.g., 'Super Shy').
        - Search: **ARTIST/GROUP NAME** (e.g., 'NewJeans').
        """
    elif category == "K-Drama":
        rule = """
        - Target(DB): **DRAMA TITLE** (e.g., 'Squid Game').
        - Search: **MAIN ACTOR NAME** (e.g., 'Lee Jung-jae').
        """
    elif category == "K-Movie":
        rule = """
        - Target(DB): **MOVIE TITLE** (e.g., 'Exhuma').
        - Search: **MAIN ACTOR NAME** (e.g., 'Choi Min-sik').
        """
    elif category == "K-Entertain":
        rule = """
        - Target(DB): **SHOW TITLE** (e.g., 'Running Man').
        - Search: **CAST MEMBER NAME** (e.g., 'Yoo Jae-suk').
        """
    else: # K-Culture
        rule = """
        - Target(DB): Place, Food, or Tradition Name (English).
        - Search: Korean Name of the Place/Food.
        - **CRITICAL**: EXCLUDE ALL IDOLS/KPOP GROUPS. Focus only on Travel/Food.
        """

    rank_prompt = f"""
    [Task]
    Analyze these {len(all_raw_items)} news titles about {category}.
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
    
    # 랭킹 저장
    db_rankings = []
    for item in rankings:
        db_rankings.append({
            "category": category,
            "rank": item.get("rank"),
            "title": item.get("display_title_en"),
            "meta_info": item.get("meta", ""),
            "score": item.get("score", 0),
            "updated_at": datetime.now().isoformat()
        })
    database.save_rankings_to_db(db_rankings)

    # 3. 타겟 선정 (도배 방지)
    print("   3️⃣ Selecting Target...")
    target_display = ""
    target_search = ""
    
    for item in rankings:
        d_title = item.get("display_title_en")
        s_word = item.get("search_keyword_kr")
        
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

    # 4. 정밀 검색
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
    - Title: Must be about '{target_display}' (Song/Drama/Place).
    - Summary: Focus on why '{target_search}' is in the news regarding '{target_display}'.

    [Output JSON]
    {{ "title": "English Title", "summary": "English Summary..." }}
    """
    
    sum_res = gemini_api.ask_gemini(summary_prompt)
    
    if sum_res:
        news_item = {
            "category": category,
            "keyword": target_display,
            "title": sum_res.get("title", f"News about {target_display}"),
            "summary": sum_res.get("summary", ""),
            "link": target_link,
            "image_url": target_image,
            "score": 100,
            "created_at": datetime.now().isoformat(),
            "likes": 0
        }
        
        database.save_news_to_live([news_item])
        database.save_news_to_archive([news_item])
        database.cleanup_old_data(category, config.MAX_ITEMS_PER_CATEGORY)
        print("   🎉 SUCCESS!")
