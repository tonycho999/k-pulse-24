import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from dateutil import parser 

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = None

def init_supabase():
    global supabase
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        except: pass

init_supabase()

def get_existing_links(category):
    if not supabase: return set()
    try:
        ago = (datetime.now() - timedelta(days=3)).isoformat()
        res = supabase.table("live_news").select("link").eq("category", category).gt("created_at", ago).execute()
        return {item['link'] for item in res.data}
    except: return set()

def save_news(news_list):
    if not supabase or not news_list: return
    try:
        # 평점이 있는 데이터만 저장
        valid_news = [n for n in news_list if n.get('score') is not None]
        if valid_news:
            supabase.table("live_news").insert(valid_news).execute()
            print(f"   ✅ 신규 {len(valid_news)}개 DB 저장 완료.")
    except Exception as e:
        print(f"❌ DB 저장 오류: {e}")

def manage_slots(category):
    """
    [규칙 5 & 6] 슬롯 관리 로직 (엄격 준수)
    1. 24시간 지난 기사 삭제 (30개 될 때까지)
    2. 그래도 많으면 점수 낮은 순 삭제
    """
    if not supabase: return

    try:
        # 전체 뉴스 가져오기
        res = supabase.table("live_news").select("*").eq("category", category).execute()
        all_items = res.data
        total_count = len(all_items)
        TARGET = 30 

        if total_count <= TARGET:
            print(f"   ✨ 현재 {total_count}개. 삭제 불필요.")
            return

        now = datetime.now()
        for item in all_items:
            try:
                item['dt'] = parser.parse(item['created_at']).replace(tzinfo=None)
            except:
                item['dt'] = now 

        # [규칙 5] 24시간 지난 기사
        old_items = [i for i in all_items if (now - i['dt']) > timedelta(hours=24)]
        
        delete_ids = []
        current_count = total_count

        # 24시간 지난 것 우선 삭제 (30개 유지하면서)
        for item in old_items:
            if current_count > TARGET:
                delete_ids.append(item['id'])
                current_count -= 1
            else:
                break 

        # [규칙 6] 그래도 30개 초과 시 점수 낮은 순 삭제
        if current_count > TARGET:
            survivors = [i for i in all_items if i['id'] not in delete_ids]
            survivors.sort(key=lambda x: x.get('score', 0)) # 오름차순 (낮은거 먼저)

            for item in survivors:
                if current_count > TARGET:
                    delete_ids.append(item['id'])
                    current_count -= 1
                else:
                    break

        if delete_ids:
            supabase.table("live_news").delete().in_("id", delete_ids).execute()
            print(f"   🧹 정리 완료: {len(delete_ids)}개 삭제. (잔여: {current_count}개)")

    except Exception as e:
        print(f"⚠️ 슬롯 관리 오류: {e}")

def archive_top_articles(): pass
def get_recent_titles(): return []
def update_keywords_db(k): pass
