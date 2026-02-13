import os
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None

def init_supabase():
    global supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try: supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except: pass

init_supabase()

def save_to_archive(news_list):
    if not supabase or not news_list: return
    try:
        archive_data = []
        for n in news_list:
            archive_data.append({
                "category": n['category'],
                "keyword": n.get('keyword'),
                "title": n['title'],
                "summary": n['summary'],
                "rank": n.get('rank'),
                "image_url": n['image_url'],
                "link": None,
                "created_at": datetime.now().isoformat()
            })
        supabase.table("search_archive").insert(archive_data).execute()
        print(f"   🏆 Archive: Top {len(archive_data)} 건 저장.")
    except Exception as e:
        print(f"   ⚠️ 아카이브 저장 실패: {e}")

def update_sidebar_rankings(category, news_list):
    if not supabase or not news_list: return
    try:
        top_10 = news_list[:10]
        ranking_data = []
        for n in top_10:
            ranking_data.append({
                "category": category,
                "rank": n['rank'],
                "keyword": n['keyword'],
                "delta": "NEW",
                "image_url": n['image_url']
            })
        supabase.table("trending_rankings").delete().eq("category", category).execute()
        if ranking_data:
            supabase.table("trending_rankings").insert(ranking_data).execute()
    except Exception as e:
        print(f"   ⚠️ Sidebar 갱신 실패: {e}")

def refresh_live_news(category, news_list):
    if not supabase or not news_list: return
    
    unique_map = {}
    for item in news_list:
        kw = item.get('keyword')
        if kw: unique_map[kw] = item
    clean_list = list(unique_map.values())
    
    final_payload = []
    for item in clean_list:
        payload = {
            "category": item.get('category'),
            "rank": item.get('rank'),
            "keyword": item.get('keyword'),
            "title": item.get('title'),
            "summary": item.get('summary'),
            "link": None,
            "image_url": item.get('image_url'),
            "score": item.get('score'),
            "likes": item.get('likes', 0),
            "dislikes": item.get('dislikes', 0),
            "published_at": item.get('published_at', datetime.now().isoformat())
        }
        final_payload.append(payload)
    
    try:
        supabase.table("live_news").delete().eq("category", category).execute()
        if final_payload:
            supabase.table("live_news").insert(final_payload).execute()
            print(f"   ✅ Live News: '{category}' {len(final_payload)}개 저장 완료.")
        update_sidebar_rankings(category, clean_list)
    except Exception as e:
        print(f"   ❌ Live News 저장 실패: {e}")
