# scraper/database.py
import os
from supabase import create_client, Client
from dotenv import load_dotenv
# 상위 폴더의 .env 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
try:
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    else:
        print("🚨 Supabase credentials missing in .env")
except Exception as e:
    print(f"🚨 Supabase Connection Error: {e}")

def save_news_to_db(data_list):
    """live_news 테이블에 저장 (컬럼: category, keyword, title, summary, link, image_url, score)"""
    if not supabase or not data_list: return

    try:
        # bulk insert (upsert)
        result = supabase.table("live_news").upsert(data_list).execute()
        print(f"   💾 Saved {len(data_list)} articles to 'live_news'.")
    except Exception as e:
        print(f"   ⚠️ DB Save Error (live_news): {e}")

def save_rankings_to_db(rank_list):
    """live_rankings 테이블에 저장 (컬럼: category, rank, title, meta_info, score)"""
    if not supabase or not rank_list: return

    try:
        result = supabase.table("live_rankings").upsert(rank_list).execute()
        print(f"   🏆 Saved rankings to 'live_rankings'.")
    except Exception as e:
        print(f"   ⚠️ DB Save Error (live_rankings): {e}")

def cleanup_old_data(category, table_name="live_news", max_limit=30):
    """카테고리별로 오래된 데이터 삭제"""
    if not supabase: return

    try:
        # 1. 현재 개수 확인
        res = supabase.table(table_name).select("id", count="exact").eq("category", category).execute()
        count = res.count

        if count > max_limit:
            # 2. 지워야 할 개수 계산
            items_to_remove = count - max_limit
            
            # 3. 오래된 순으로 ID 조회 (created_at 기준)
            # live_rankings는 updated_at, live_news는 created_at 사용
            sort_col = "updated_at" if table_name == "live_rankings" else "created_at"
            
            old_rows = supabase.table(table_name)\
                .select("id")\
                .eq("category", category)\
                .order(sort_col, desc=False)\
                .limit(items_to_remove)\
                .execute()
            
            ids = [row['id'] for row in old_rows.data]
            
            if ids:
                supabase.table(table_name).delete().in_("id", ids).execute()
                print(f"   🧹 Cleaned up {len(ids)} old items from '{table_name}'.")
                
    except Exception as e:
        print(f"   ⚠️ Cleanup Error: {e}")
