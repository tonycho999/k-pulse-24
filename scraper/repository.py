from datetime import datetime, timedelta
from dateutil.parser import isoparse
from config import supabase, CATEGORY_MAP

def get_existing_links(category):
    # 중복 체크를 위해 해당 카테고리의 모든 링크 조회
    res = supabase.table("live_news").select("link").eq("category", category).execute()
    return {item['link'] for item in res.data}

def save_news(news_list):
    """
    뉴스 저장: 중복 제거 및 4.0점 미만 기사 필터링
    """
    if not news_list: return
    
    seen_links = set()
    unique_list = []
    
    for item in news_list:
        # [규칙 3] 4점 미만 기사는 저장하지 않음
        if item.get('score', 0) < 4.0:
            continue

        if item['link'] not in seen_links:
            unique_list.append(item)
            seen_links.add(item['link'])
            
    if not unique_list:
        print("   ℹ️ 저장할 기사가 없습니다 (모두 중복이거나 4점 미만).")
        return

    try:
        supabase.table("live_news").upsert(unique_list, on_conflict="link").execute()
        print(f"   ✅ 신규 {len(unique_list)}개 DB 저장 완료 (4점 이상).")
    except Exception as e:
        print(f"   ⚠️ 저장 실패: {e}")

def manage_slots(category):
    """
    [규칙 5, 6, 7] 30개 슬롯 유지 관리 로직 (랭킹 업데이트 포함)
    """
    # 1. 해당 카테고리의 모든 기사를 가져옴
    res = supabase.table("live_news").select("*").eq("category", category).execute()
    all_articles = res.data
    total_count = len(all_articles)
    
    print(f"   📊 {category.upper()}: 현재 {total_count}개 (목표: 30개)")

    # 30개 이하라면 삭제 로직 불필요 -> 바로 랭킹만 업데이트
    if total_count <= 30:
        _update_rankings(all_articles)
        return

    # --- 삭제 로직 시작 ---
    delete_ids = []
    now = datetime.now()
    threshold = now - timedelta(hours=24) # 24시간 기준
    
    # 기사 정렬: 날짜순 (오래된 것 식별용)
    try: 
        all_articles.sort(key=lambda x: isoparse(x['created_at']).replace(tzinfo=None))
    except: pass

    remaining_count = total_count
    
    # [규칙 5] 24시간 지난 기사 우선 삭제 (단, 30개 될 때까지만)
    for art in all_articles:
        if remaining_count <= 30: break # 30개 도달 시 즉시 중단
        
        try: art_date = isoparse(art['created_at']).replace(tzinfo=None)
        except: art_date = datetime(2000, 1, 1)

        if art_date < threshold:
            delete_ids.append(art['id'])
            remaining_count -= 1

    # [규칙 6] 그래도 30개가 넘으면 점수 낮은 순 삭제
    if remaining_count > 30:
        survivors = [a for a in all_articles if a['id'] not in delete_ids]
        # 점수 오름차순 정렬 (낮은 점수부터 삭제)
        survivors.sort(key=lambda x: x.get('score', 0))
        
        for art in survivors:
            if remaining_count <= 30: break
            delete_ids.append(art['id'])
            remaining_count -= 1

    # 실제 삭제 실행
    if delete_ids:
        supabase.table("live_news").delete().in_("id", delete_ids).execute()
        print(f"   🧹 공간 확보: {len(delete_ids)}개 삭제 완료 (현재 {remaining_count}개 유지).")
    
    # [규칙 7] 삭제 완료 후 남은 기사들에 대해 Rank 재산정 및 업데이트
    final_survivors = [a for a in all_articles if a['id'] not in delete_ids]
    _update_rankings(final_survivors)

def _update_rankings(articles):
    """
    남은 기사들을 점수순(내림차순)으로 정렬하여 rank(1~30) 업데이트
    """
    if not articles: return

    # 점수 높은 순 정렬
    articles.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    updates = []
    for i, art in enumerate(articles):
        new_rank = i + 1
        if art.get('rank') != new_rank:
            updates.append({"id": art['id'], "rank": new_rank})
            
    if updates:
        try:
            supabase.table("live_news").upsert(updates).execute()
            print(f"   🔄 {len(updates)}개 기사 랭킹(Rank) 재정렬 완료.")
        except Exception as e:
            print(f"   ⚠️ 랭킹 업데이트 실패: {e}")

def archive_top_articles():
    """상위 랭크(Top 10) 기사 아카이빙"""
    print("🗄️ 상위 랭크(Top 10) 기사 아카이빙 시작...")
    
    for category in CATEGORY_MAP.keys():
        # [핵심 수정] rank가 0보다 크고 10 이하인 것 조회
        res = supabase.table("live_news")\
            .select("*")\
            .eq("category", category)\
            .lte("rank", 10)\
            .gt("rank", 0)\
            .order("rank", desc=False)\
            .execute()
            
        top_articles = res.data
        if top_articles:
            try:
                # search_archive 테이블에 저장할 데이터 매핑
                archive_data = []
                for art in top_articles:
                    archive_data.append({
                        "created_at": art['created_at'],
                        "category": art['category'],
                        "title": art['title'],
                        "summary": art['summary'],
                        "image_url": art['image_url'],
                        "original_link": art['link'],  # live_news의 link를 archive의 original_link로 저장
                        "score": art['score'],
                        "rank": art['rank']
                    })
                
                # 링크(original_link) 기준으로 중복 방지(upsert)
                supabase.table("search_archive").upsert(archive_data, on_conflict="original_link").execute()
                print(f"   💾 {category.upper()}: Top {len(archive_data)}개 -> 아카이브 저장 완료.")
            except Exception as e:
                print(f"   ⚠️ 아카이브 저장 실패 ({category}): {e}")

def update_keywords_db(keywords):
    if not keywords: return
    try:
        supabase.table("trending_keywords").delete().neq("id", 0).execute()
    except: pass 
    
    insert_data = []
    for i, item in enumerate(keywords):
        insert_data.append({
            "keyword": item.get('keyword'),
            "count": item.get('count', 0),
            "rank": item.get('rank', i + 1),
            "updated_at": datetime.now().isoformat()
        })
    
    if insert_data:
        try:
            supabase.table("trending_keywords").insert(insert_data).execute()
            print("   ✅ 키워드 랭킹 DB 업데이트 완료.")
        except Exception as e:
            print(f"   ⚠️ 키워드 저장 실패: {e}")

def get_recent_titles(limit=100):
    res = supabase.table("live_news").select("title").order("created_at", desc=True).limit(limit).execute()
    return [item['title'] for item in res.data]
