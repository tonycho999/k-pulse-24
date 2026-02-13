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
        # live_news 중복 체크 (최근 3일)
        ago = (datetime.now() - timedelta(days=3)).isoformat()
        res = supabase.table("live_news").select("link").eq("category", category).gt("created_at", ago).execute()
        return {item['link'] for item in res.data}
    except: return set()

def save_news(news_list):
    """
    뉴스 저장 로직:
    1. 모든 뉴스 -> live_news 테이블 저장
    2. 평점 7.0 이상 -> search_archive 테이블 추가 저장
    """
    if not supabase or not news_list: return
    
    try:
        # 1. live_news 저장 (실시간용)
        # score가 없는 경우 대비해 기본값 처리
        valid_news = []
        for n in news_list:
            if n.get('score') is None: n['score'] = 5.0
            valid_news.append(n)

        if valid_news:
            supabase.table("live_news").insert(valid_news).execute()
            print(f"   ✅ Live News: {len(valid_news)}개 저장 완료.")
            
            # 2. search_archive 저장 (보관용, 평점 7.0 이상)
            # 고득점 기사만 필터링
            high_quality_news = [n for n in valid_news if n['score'] >= 7.0]
            
            if high_quality_news:
                # search_archive 테이블에 저장 (에러나도 live_news는 성공했으니 무시)
                try:
                    supabase.table("search_archive").insert(high_quality_news).execute()
                    print(f"   🏆 Archive: 평점 7.0 이상 {len(high_quality_news)}개 아카이브 저장 완료.")
                except Exception as e:
                    print(f"   ⚠️ 아카이브 저장 실패 (중복 등): {e}")

    except Exception as e:
        print(f"❌ DB 저장 오류: {e}")

def manage_slots(category):
    """
    슬롯 관리 (30개 유지):
    1. 24시간 지난 기사 삭제
    2. 30개 초과 시 점수 낮은 순 삭제
    """
    if not supabase: return

    try:
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

        # [1] 24시간 지난 기사 식별
        old_items = [i for i in all_items if (now - i['dt']) > timedelta(hours=24)]
        
        delete_ids = []
        current_count = total_count

        # 24시간 지난 것 우선 삭제
        for item in old_items:
            if current_count > TARGET:
                delete_ids.append(item['id'])
                current_count -= 1
            else:
                break 

        # [2] 그래도 30개 초과 시 점수 낮은 순 삭제
        if current_count > TARGET:
            survivors = [i for i in all_items if i['id'] not in delete_ids]
            survivors.sort(key=lambda x: x.get('score', 0)) # 오름차순 (낮은 점수부터)

            for item in survivors:
                if current_count > TARGET:
                    delete_ids.append(item['id'])
                    current_count -= 1
                else:
                    break

        if delete_ids:
            supabase.table("live_news").delete().in_("id", delete_ids).execute()
            print(f"   🧹 정리 완료: {len(delete_ids)}개 삭제 (잔여: {current_count}개)")

    except Exception as e:
        print(f"⚠️ 슬롯 관리 오류: {e}")

def get_recent_titles():
    if not supabase: return []
    try:
        res = supabase.table("live_news").select("title").order("created_at", desc=True).limit(50).execute()
        return [item['title'] for item in res.data]
    except: return []

def update_keywords_db(keywords):
    # 키워드 저장 로직 (필요시 구현)
    pass
