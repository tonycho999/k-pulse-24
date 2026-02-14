# scraper/processor.py
import time
from datetime import datetime
import config
import naver_api
import gemini_api
import database

def run_category_process(category):
    print(f"\n🚀 [Processing] Category: {category}")

    # 1. 뉴스 수집
    queries = config.SEARCH_QUERIES.get(category, [])
    all_raw_items = []
    seen_links = set()

    print(f"   1️⃣ Fetching news with 3 queries...")
    if not queries:
        print("      ⚠️ No queries defined.")
        return

    for q in queries:
        # [중요] 최신순 정렬(date) 필수
        items = naver_api.search_news_api(q, display=20)
        for item in items:
            if item['link'] not in seen_links:
                seen_links.add(item['link'])
                all_raw_items.append(item)
        time.sleep(0.5)

    if not all_raw_items:
        print("   ❌ [Stop] No items found.")
        return

    print(f"      ✅ Total collected articles: {len(all_raw_items)}")
    
    # 2. 랭킹 선정
    print("   2️⃣ Extracting Keywords (Subject vs Person)...")
    
    # 프롬프트 규칙 (기존과 동일)
    if category == "K-Pop":
        rule = "Target(DB): SONG TITLE / Search: ARTIST NAME"
    elif category == "K-Drama":
        rule = "Target(DB): DRAMA TITLE / Search: ACTOR NAME. Pick CURRENTLY AIRING dramas only."
    elif category == "K-Movie":
        rule = "Target(DB): MOVIE TITLE / Search: ACTOR NAME. Pick CURRENT/UPCOMING movies."
    elif category == "K-Entertain":
        rule = "Target(DB): SHOW TITLE / Search: CAST MEMBER."
    else:
        rule = "Target(DB): Place/Food Name. Search: Korean Name. EXCLUDE IDOLS."

    rank_prompt = f"""
    [Task]
    Analyze these {len(all_raw_items)} news titles.
    Extract Top 10 trends.
    Rules: {rule}
    Output JSON ONLY: {{ "rankings": [ {{ "rank": 1, "display_title_en": "Title", "search_keyword_kr": "SearchWord", "meta": "info", "score": 95 }} ] }}
    
    [News Titles]
    {str([item['title'] for item in all_raw_items])}
    """
    
    rank_res = gemini_api.ask_gemini(rank_prompt)
    
    # [수정됨] 여기서 실패하면 이유를 말하고 종료
    if not rank_res or "rankings" not in rank_res:
        print("   ❌ [Stop] AI failed to extract rankings. (JSON Error or Empty)")
        return

    rankings = rank_res.get("rankings", [])[:10]
    
    # DB 저장
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

    # 3. 타겟 선정
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

    if not full_texts: 
        print("   ❌ [Stop] Failed to crawl details.")
        return

    # 5. 요약 작성
    print(f"   5️⃣ Summarizing '{target_display}'...")
    summary_prompt = f"""
    [Task]
    Write a news summary in ENGLISH about '{target_display}' involving '{target_search}'.
    Sources: {str(full_texts)[:6000]}
    Output JSON: {{ "title": "English Title", "summary": "English Summary" }}
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
    else:
        print("   ❌ [Stop] AI Summary Failed.")
