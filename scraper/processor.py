# scraper/processor.py
import time
from datetime import datetime
import config
import naver_api
import gemini_api
import database

def run_category_process(category):
    print(f"\n🚀 [Processing] Category: {category}")

    # STEP 1: 네이버 검색
    keyword = config.SEARCH_KEYWORDS.get(category)
    print(f"   1️⃣ Searching Naver for '{keyword[:10]}...'")
    
    raw_items = naver_api.search_news_api(keyword, display=100)
    
    if not raw_items:
        print("   ❌ [Stop] No items found from Naver API. (Check Naver Keys)")
        return

    titles = "\n".join([f"- {item['title']}" for item in raw_items])
    print(f"   ✅ Found {len(raw_items)} articles.")

    # STEP 2: 랭킹 선정
    print("   2️⃣ Asking AI for Ranking...")
    rank_prompt = f"""
    [Task]
    Analyze news titles about {category}.
    Identify Top 10 trending keywords.
    Output JSON: {{ "rankings": [ {{ "rank": 1, "keyword": "Name", "meta": "Info", "score": 95 }} ] }}
    """
    
    rank_res = gemini_api.ask_gemini(rank_prompt)
    
    if not rank_res: 
        print("   ❌ [Stop] AI returned NO ranking data. (Check Gemini Key/Quota)")
        return

    rankings = rank_res.get("rankings", [])[:10]
    print(f"   ✅ AI identified {len(rankings)} trends.")
    
    # DB 저장 (랭킹)
    db_rankings = []
    for item in rankings:
        db_rankings.append({
            "category": category,
            "rank": item.get("rank"),
            "title": item.get("keyword"),
            "meta_info": item.get("meta", ""),
            "score": item.get("score", 0),
            "updated_at": datetime.now().isoformat()
        })
    database.save_rankings_to_db(db_rankings)

    # STEP 3: 타겟 선정 (도배 방지)
    print("   3️⃣ Selecting Target Keyword...")
    target_keyword = ""
    
    for item in rankings:
        candidate = item.get("keyword")
        if database.is_keyword_used_recently(category, candidate, hours=4):
            print(f"      - Skip '{candidate}' (Cooldown)")
        else:
            print(f"      - Selected: '{candidate}'")
            target_keyword = candidate
            break
    
    if not target_keyword and rankings:
        target_keyword = rankings[0].get("keyword")
        print(f"      ⚠️ All cooldown. Forced: '{target_keyword}'")

    if not target_keyword: return

    # STEP 4: 정밀 수집
    print(f"   4️⃣ Deep Diving into '{target_keyword}'...")
    target_items = naver_api.search_news_api(target_keyword, display=3)
    
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
        print("   ❌ [Stop] Failed to crawl articles.")
        return

    # STEP 5: 기사 작성
    print("   5️⃣ Writing Summary...")
    summary_prompt = f"""
    [Articles about '{target_keyword}']
    {str(full_texts)[:6000]}

    [Task]
    Write a high-quality news summary in Korean.
    [Output JSON]
    {{ "title": "Title", "summary": "Summary" }}
    """
    
    sum_res = gemini_api.ask_gemini(summary_prompt)
    
    if sum_res:
        news_item = {
            "category": category,
            "keyword": target_keyword,
            "title": sum_res.get("title", f"{target_keyword} 이슈"),
            "summary": sum_res.get("summary", ""),
            "link": target_link,
            "image_url": target_image,
            "score": 100,
            "created_at": datetime.now().isoformat(),
            "likes": 0
        }
        
        # STEP 6: 저장
        print("   6️⃣ Saving to DB...")
        database.save_news_to_live([news_item])
        database.save_news_to_archive([news_item])
        database.cleanup_old_data(category, config.MAX_ITEMS_PER_CATEGORY)
        print("   🎉 SUCCESS!")
    else:
        print("   ❌ [Stop] AI failed to write summary.")
